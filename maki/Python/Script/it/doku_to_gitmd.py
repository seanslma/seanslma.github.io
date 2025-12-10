import os
import re

'''
convert dokuwiki pages to git markdown files
'''

diro = r'C:\data\pages'
diri = r'C:\wiki\data\pages'
path = 'python/it'

def main():
    for file in getfiles(os.path.join(diri,path)):
        replace(file, f'{file.replace(diri, diro)[:-4]}.md')

def replace(fi, fo):
    txt = readfile(fi)

    #header
    txt = re.sub('^======\s*(.*?)\s*======', r'# \1', txt, flags = re.M)
    txt = re.sub('^=====\s*(.*?)\s*=====', r'## \1', txt, flags = re.M)
    txt = re.sub('^====\s*(.*?)\s*====', r'### \1', txt, flags = re.M)
    txt = re.sub('^===\s*(.*?)\s*===', r'#### \1', txt, flags = re.M)
    txt = re.sub('^==\s*(.*?)\s*==', r'##### \1', txt, flags = re.M)

    #code
    txt = re.sub('^<code\s*(.*?)\s*>(.*?)^</code>', r'```\1\2```', txt, flags = re.M+re.DOTALL)

    #image
    txt = re.sub('\{\{(.*?)\|(.*?)\}\}', r'[[\1]]', txt)

    #link
    txt = re.sub('\[\[(.*?)\|(.*?)\]\]', r'[\2](\1)', txt)

    writefile(fo, txt)

def mkdirs(dir):
    if not os.path.isdir(dir):
        os.makedirs(dir)

def getfiles(dir):
    files = []
    for (dirpath, dirnames, filenames) in os.walk(dir):
        files += [os.path.join(dirpath, file) for file in filenames if file[-4:]=='.txt']
    return files

def readfile(fi):
    with open(fi, 'r', encoding='utf-8') as f:
        txt = f.read()
    return txt

def writefile(fo, txt):
    mkdirs(os.path.dirname(fo))
    with open(fo, 'w', encoding='utf-8') as f:
        f.write(txt)

if __name__ == '__main__':
    main()
