import xml.etree.ElementTree as ET
import textwrap
import sys
import re
kwds = ['src']
def getparams(xml):
    pattern = re.compile('\{([^\{\}]+)\}')
    params = []
    if xml.text is not None:
        params += pattern.findall(xml.text)
    for child in xml:
        params += getparams(child)
    return params
def removeparams(text):
    pattern = '\{([^\{\}]+)\}'
    def getname(str):
        return str.group(1).split(":")[1].strip()
    pat = re.compile(pattern)
    return re.sub(pattern, getname, text)
def processContainer(xml):
    res = ""
    res += "return Container(\n"
    for style in xml.attrib:
        if style == 'bg':
            res += f"\tcolor: Colors.{xml.attrib['bg']},\n"
    for prop in xml[:-1]:
        res += "\t" + process_xml(prop) + ",\n"
    res += "\tchild: " + process_xml(xml[-1]) + ",\n"
    res += ");"
    return res

def processMargin(xml):
    res = ""
    res += "margin: "
    if "all" in xml.attrib:
        res += f"EdgeInsets.all({xml.attrib['all']})"
    else:
        raise Exception("margin tag must contain one of the following: 'left', 'right', 'top', 'bottom', 'horizontal', 'vertical', 'all'")
    return res

def processPadding(xml):
    res = ""
    res += "padding: "
    if "all" in xml.attrib:
        res += f"EdgeInsets.all({xml.attrib['all']})"
    else:
        raise Exception("padding tag must contain one of the following: 'left', 'right', 'top', 'bottom', 'horizontal', 'vertical', 'all'")
    return res

def processText(xml):
    styles = []
    for style in xml.attrib:
        if style == 'size':
            styles.append(f"fontSize: {xml.attrib['size']}")
    return f"Text({removeparams(xml.text)}, style: TextStyle({','.join(styles)}))"

def processWidget(xml):
    if len(xml) > 1:
        print("Warning: only first child of 'Widget' will be processed.")
    params = getparams(xml)
    formattedparams = [""]
    paramdecls = []
    for param in params:
        spl = param.split(':')
        name = spl[1].strip()
        formattedparams.append(f"required this.{name}")
        if spl[0].strip() == 'str':
            paramdecls.append(f"final String {name};")
    declconcat = "\n\t\t".join(paramdecls)
    return f"""class {xml.attrib['name']} extends StatelessWidget {{
    {xml.attrib['name']}({{Key? key{", ".join(formattedparams)}}}) : super(key: key);
    {declconcat}
    @override
    Widget build(BuildContext context) {{
{textwrap.indent(process_xml(xml[0]), '        ')}
    }}
}}"""

def processMain(xml):
    imports = ""
    processedimports = []
    for child in xml:
        if 'src' in child.attrib:
            if child.attrib['src'] in processedimports:
                continue
            parse_file(child.attrib['src'])
            imports += f"import '{child.attrib['src']}.dart';\n"
            processedimports.append(child.attrib['src'])
    body = process_xml(xml[-1])
    return imports + f"""
void main() {{
  runApp(const MyApp());
}}

class MyApp extends StatelessWidget {{
  const MyApp({{Key? key}}) : super(key: key);
  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{xml.attrib.get('title') or 'Flap app'}',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: const MyHomePage(title: '{xml.attrib.get('title') or 'Flap app'}'),
    );
  }}
}}

class MyHomePage extends StatefulWidget {{
  const MyHomePage({{Key? key, required this.title}}) : super(key: key);

  final String title;

  @override
  State<MyHomePage> createState() => _MyHomePageState();
}}

class _MyHomePageState extends State<MyHomePage> {{
  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.title),
      ),
      body: {body},
    );
  }}
}}
"""

def process_xml(xml):
    if f"process{xml.tag}" not in globals():
        params = []
        for param in xml.attrib:
            if param in kwds:
                continue
            params.append(f"{param}: '{xml.attrib[param]}'")
        return f"{xml.tag}({', '.join(params)})"
    return globals()[f"process{xml.tag}"](xml)

def parse_file(filename):
    tree = ET.parse(f"{filename}.xml")
    root = tree.getroot()
    fo = open(f"src/lib/{filename}.dart", "w")
    fo.write("import 'package:flutter/material.dart';\n")
    fo.write(process_xml(root))
tree = ET.parse("test.xml").getroot()
print(getparams(tree))
if len(sys.argv) == 1:
    parse_file("main")
else: 
    parse_file(sys.argv[1])