#coding=utf8
import os
import copy
import configparser
import shutil
import json
import xml.dom.minidom
from slpp import slpp as lua
import io
StringIO = io.StringIO()

def log(log):
    print(log)

def debug(log):
    print(log)

def error(log):
    print('components error:')
    print(log)

def remove_BOM(path):
    f = open(path,'r')
    s = f.read()
    u = s.decode('utf-8-sig')
    s = u.encode('utf-8')
    f.close()
    f = open(path,'w')
    f.write(s)
    f.close()

def isPathInPaths(path, paths):
    for pp in paths:
        if pp in path:
            return True
    return False

def writeDictToJson(conJsonPath, dict_published, bOverWritten):
    dictCfg = {}
    if not bOverWritten:
        if os.path.exists(conJsonPath):
            with open(conJsonPath) as jsonFile:
                try:
                    dictCfg = json.load(jsonFile)
                except Exception as r:
                    print(r)
        extendDict(dict_published, dictCfg)
    else:
        dictCfg = dict_published

    if not os.path.exists(os.path.dirname(conJsonPath)):
        os.makedirs(os.path.dirname(conJsonPath))
    with open(conJsonPath, 'wb') as file:
        strJson = json.dumps(dictCfg, sort_keys=True, indent=4, separators=(',',':'))
        file.write(strJson)
        file.close()

def getDictFromXml(xmlPath):
    local_dict = {}
    def get(node):
        node_dict = {}
        for name, value in node.attributes.items():
            node_dict[name] = value
        for child in node.childNodes:
            if child.nodeType == xml.dom.Node.ELEMENT_NODE:
                child_dict = []
                if not child.tagName in node_dict:
                    node_dict[child.tagName] = []
                node_dict[child.tagName].append(get(child))
        return node_dict

    if os.path.exists(xmlPath):
        dom = xml.dom.minidom.parse(xmlPath)
        root = dom.documentElement
        local_dict = get(root)
    return local_dict

def writeDictToXml(xmlPath, local_dict):
    def listToXml(dom, parent, name, value_list):
        for value in value_list:
            if type(value) is dict:
                parent.appendChild(dictToXml(dom, name, value))
            elif type(value) is list:
                node = dom.createElement(name)
                parent.appendChild(node)
                listToXml(dom, node, 'value', value)
            else:
                parent.appendChild(dom.createTextNode(value))

    def dictToXml(dom, name, node_dict):
        node = dom.createElement(name)
        for key, value in node_dict.items():
            if type(value) is dict:
                node.appendChild(dictToXml(dom, key, value))
            elif type(value) is list:
                listToXml(dom, node, key, value)
            else:
                node.setAttribute(key, value)

        return node

    dom = xml.dom.minidom.Document()
    root_node = dictToXml(dom, 'root', local_dict)
    dom.appendChild(root_node)
    with open(xmlPath, 'w') as file:
        dom.writexml(file,addindent='\t',newl='\n')
        file.close()

def mergeDictToXml(xmlPath, dict_published, willMergeOld=True, nodeName='Node'):
    local_dict = {}
    if willMergeOld:
        try:
            local_dict = getDictFromXml(xmlPath)
        except Exception as r:
            print(r)

    local_nodes = []
    if 'Node' in local_dict:
        local_nodes = local_dict['Node']
    for id, files in dict_published.items():
        for file in files:
            local_node_found = None
            bNeedAppendFile = True
            for local_node in local_nodes:
                if 'id' in local_node and local_node['id'] == id:
                    local_node_found = local_node
                    if 'add' in local_node:
                        local_adds = local_node['add']
                        for local_add in local_adds:
                            if 'file' in local_add and local_add['file'] == file:
                                bNeedAppendFile = False
                                break
                    break
            if bNeedAppendFile:
                if None == local_node_found:
                    local_node_found = {'id' : id, 'add' : []}
                    local_nodes.append(local_node_found)
                if not 'add' in local_node_found:
                    local_node_found['add'] = []
                local_node_found['add'].append({'file' : file})
    local_dict['Node'] = local_nodes

    try:
        local_dict['Node'].sort(key=lambda d:d['id'])
    except Exception as r:
        print(r)

    return local_dict

def mergeExtDictToXml(xmlPath, ext_dict, require_name, require_level):
    str_level = str(require_level)
    local_dict = {}
    try:
        local_dict = getDictFromXml(xmlPath)
    except Exception as r:
        print(r)

    dict_require = None
    for key, vv in local_dict.items():
        for value in vv:
            if 'level' in value and value['level'] == str_level:
                dict_require = value
                break
    if None == dict_require:
        dict_require = { 'level' : str_level }
        local_dict[require_name] = dict_require

    if not 'component' in dict_require:
        dict_require['component'] = []
    for name, value in ext_dict.items():
        isInserted = False
        for index in range(len(dict_require['component'])):
            com = dict_require['component'][index]
            if 'name' in com and com['name'] == name:
                for key, vv in value.items():
                    dict_require['component'][index][key] = vv
                isInserted = True
                break
        if not isInserted:
            dict_require['component'].append(value)

    try:
        dict_require['component'].sort(key=lambda d:d['name'])
    except Exception as r:
        print(r)
    writeDictToXml(xmlPath, local_dict)

def extendDict(src_dict, dst_dict, willSort=True):
    for key, l in src_dict.items():
        if key in dst_dict:
            if type(dst_dict[key]) is list:
                dst_dict[key].extend(l)
                dst_dict[key] = list(set(dst_dict[key]))
            else:
                extendDict(l, dst_dict[key], willSort)
        else:
            dst_dict[key] = copy.deepcopy(l)
        if willSort:
            dst_dict[key].sort()

def getArtSplitNamesInIni(name, ini_path):
    split_names = []
    if None != ini_path:
        ini = ConfigParser.ConfigParser()
        ini.read(ini_path)
        if ini.has_section(name):
            nSize = ini.getint(name, 'size')
            for i in range(1, nSize + 1):
                split_names.append(ini.get(name, str(i)))
    return split_names

def AppendCfgFilesMd5(cfg_files, src_path, abs_path, will_remove):
    src_path = src_path.replace('//', '/')
    abs_path = abs_path.replace('//', '/')
    if os.path.exists(src_path):
        for cfg in cfg_files:
            if cfg['dst'] == abs_path:
                return

        cfg = {'src' : src_path, 'dst' : abs_path, 'remove' : will_remove}
        cfg_files.append(cfg)

def appendCfgFilesMd5InSplitArtsListIni(cfg_files, rel_path, src_path, dst_path, willRemove, ini_path=None):
    _dir, _name = os.path.split(rel_path)
    _list_name = getArtSplitNamesInIni(_name, ini_path)
    if 0 == len(_list_name):
        _list_name.append(_name)
    for name in _list_name:
        rel_path = _dir + '/' + name
        AppendCfgFilesMd5(cfg_files, src_path + rel_path, dst_path + rel_path, willRemove)

def getCustomPriorityIni(ini_path):
    dict_priority = {}
    priority_ini = ConfigParser.ConfigParser()
    file = open(ini_path, 'rb')
    content = file.read().decode('utf-8-sig').encode('utf8')
    priority_ini.readfp(StringIO.StringIO(content))

    section = 'priority'
    if priority_ini.has_section(section):
        for item in priority_ini.items(section):
            dict_priority[item[0]] = item[1]
    return dict_priority

def mergeExtComponentsXml(dict_published, workingPath, ext_components, priority_key, require_name, require_level):
    if 0 < len(dict_published.keys()) and 'render_suffix' in ext_components and 'ExtComponentsPath' in ext_components:
        ext_components_path = workingPath + ext_components['ExtComponentsPath']
        render_suffix = ext_components['render_suffix']

        custom_priority_path = ''
        if 'ExtCustomPriorityPath' in ext_components:
            custom_priority_path = workingPath + ext_components['ExtCustomPriorityPath']

        priority = None
        if priority_key in ext_components:
            priority = ext_components[priority_key]

        custom_priority = {}
        if '' != custom_priority_path:
            custom_priority = getCustomPriorityIni(custom_priority_path)

        dict_ext = {}
        for key, value in dict_published.items():
            dict_ext[key] = { 'name' : key }
            if key in custom_priority:
                dict_ext[key]['priority'] = custom_priority[key]
            elif None != priority:
                dict_ext[key]['priority'] = priority
            for gltype, suffix in render_suffix.items():
                if 'ignore_gles' in value and '1' == value['ignore_gles']:
                    dict_ext[key][gltype] = key
                else:
                    dict_ext[key][gltype] = key + suffix
        mergeExtDictToXml(ext_components_path, dict_ext, require_name, require_level)

def getLuaLinesOfTable(lua_path, tableName):
    if not os.path.exists(lua_path):
        return ''

    with open(lua_path, 'rb') as file:
        lines = file.readlines()

        table_lines = b''
        bBracket = b''
        bBracketReverse = b''
        nCountBrackets = -1
        for line in lines:
            while True:
                index_left = line.find(b'--[[')
                if index_left != -1:
                    index_right = line.find(b']]', index_left + 4)
                    if index_right != -1:
                        lineLeft = line[0 : index_left]
                        lineRight = line[index_right + 2:]
                        line = lineLeft + lineRight
                    else:
                        break
                else:
                    break
            
            index_content = line.find(b'--')
            if -1 != index_content:
                line = line[0 : index_content]
            if -1 == nCountBrackets:
                index_1 = line.find(tableName)
                if -1 != index_1:
                    nCountBrackets = 0

            if -1 != nCountBrackets:
                if b'' == bBracket:
                    index_1 = line.find(tableName) + len(tableName)
                    index = 0
                    for i in range(index_1, len(line)):
                        if line[i] == b'{':
                            bBracket = b'{'
                            bBracketReverse = b'}'
                            index = i
                            break
                        elif line[i] == b'[':
                            bBracket = b'['
                            bBracketReverse = b']'
                            index = i
                            break
                    line = line[index : ]

                if b'' != bBracket:
                    nCountBrackets = nCountBrackets + line.count(bBracket) - line.count(bBracketReverse)
                    if 0 == nCountBrackets:
                        index = line.rfind(bBracketReverse)
                        line = line[ : index + 1]
                    elif 0 > nCountBrackets:
                        for index in range(len(line) - 1, -1, -1):
                            c = line[index]
                            if bBracketReverse == c:
                                nCountBrackets = nCountBrackets + 1
                            if 0 == nCountBrackets:
                                break
                        line = line[ : index]

                    #line = line.replace(b'\r', b'').replace(b'\n', b'').replace(b'\t', b'')
                    table_lines = table_lines + line
                    if 0 >= nCountBrackets:
                        break

        return table_lines

    return ''
    
def getLuaTableToDict(lua_path, tableName):
    table_lines = getLuaLinesOfTable(lua_path, tableName)
    if 0 < len(table_lines):
        return lua.decode(table_lines)
    else:
        return {}

class MyConfigParser(configparser.ConfigParser):
    def __init__(self, defaults=None):
        ConfigParser.ConfigParser.__init__(self, defaults=defaults)
    def optionxform(self, optionstr):
        return optionstr

def getConfigParser(iniPath):
    if os.path.exists(iniPath):
        try:
            myConfigParser = MyConfigParser()
            file = open(iniPath, 'rb')
            content = file.read().decode('utf-8-sig').encode('utf8')
            myConfigParser.readfp(StringIO.StringIO(content))
            return myConfigParser
        except Exception as e:
            print(e)

    return None

def writeDictToIni(dict_values, ini_path):
    with open(ini_path, b'w') as iniFile:
        configWriter = MyConfigParser()
        sorted_sections = sorted(dict_values.keys())
        for section in sorted_sections:
            configWriter.add_section(section)

            section_value = dict_values[section]
            sorted_keys = sorted(section_value.keys())
            for key in sorted_keys:
                configWriter.set(section, key, section_value[key])

        configWriter.write(iniFile)
        iniFile.close()