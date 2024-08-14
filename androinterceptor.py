import os
from subprocess import Popen, PIPE, STDOUT
import xmltodict
import xmlformatter
import shutil
import sys

# import pprint
# pp = pprint.PrettyPrinter(indent=4)

cmds = {'unpack': 'apktool d -o out -f {}', # apk name
        'repack': 'apktool b out -o {} -use-aapt2', # output apk name
        'sign': 'jarsigner -sigalg SHA1withRSA -digestalg SHA1 -keystore ../certs/rebel.keystore '
                '{} rebel --storepass "rebelme" --keypass "rebelme"', # apk name to sign
        'zip': 'zipalign -v 4 {} {}', # src apk name, dst apk name post zip align
        }

extract = {'permissions': ['manifest', 'uses-permission'],
           'activities': ['manifest', 'application', 'activity'],
           'services': ['manifest', 'application', 'service'],
           'providers': ['manifest', 'application', 'provider'],
           'receivers': ['manifest', 'application', 'receiver']}

network_security_config = 'network_security_config'


def run_cmd(cmd, *args):
    print('command being executed "{}"'.format(str(cmd).format(*args)))
    try:
        res = Popen(str(cmd).format(*args), stdout=PIPE, stderr=STDOUT, shell=True)
    except Exception as e:
        print(e)
        exit(0)
    out = res.communicate()[0]
    if res.returncode != 0:
        print(f"Failed {out.decode('utf-8')}")
        exit(0)
    return


def edit_manifest(filename=''):
    print('Inside {}'.format('edit_manifest'))
    formatter = xmlformatter.Formatter(indent="1", indent_char="\t", encoding_output="utf-8", preserve=["literal"])

    with open('out'+'/AndroidManifest.xml', 'r') as fd:
        x = xmltodict.parse(fd.read())

    pkg_name = x['manifest']['@package']
    print('***************** The package name is : {} *****************'.format(pkg_name))

    for each, subscripts in extract.items():
        # print('~~~~~~~~~~~~~~~~~ The app {} are ~~~~~~~~~~~~~'.format(each))
        a = x
        for subscript in subscripts:
            a = a[subscript]
        if not isinstance(a, list):
            lst = list()
            lst.append(a)
            a = lst
        for i in a:
            if each not in ['permissions', 'providers']:
                i['@android:exported'] = 'true'
            print(i['@android:name'])
    # pp.pprint(x)

    x['manifest']['application']['@android:debuggable'] = 'true'
    x['manifest']['application']['@android:allowBackup'] = 'true'
    x['manifest']['application']['@android:networkSecurityConfig'] = '@xml/'+network_security_config

    shutil.copy(os.path.join('../configs', network_security_config+'.xml'), os.path.join('out', 'res/xml'))
    out = formatter.format_string(xmltodict.unparse(x)).decode('utf-8')
    with open(os.path.join('out', 'AndroidManifest.xml'), mode='w', encoding='utf-8') as fd:
        fd.write(out)
    return pkg_name


if __name__ == '__main__':
    src = sys.argv[1]
    os.chdir(os.environ['HOME']+'/teamstreamz/apk')

    apk_path, apkname = src.rsplit('/', maxsplit=1)
    apk_in = apkname.rsplit('.', maxsplit=1)[0]

    try:
        shutil.rmtree('tmp', ignore_errors=True)
        filename = os.path.join(apk_path, apk_in+'_intercept.apk')
        if os.path.isfile(filename):
            os.remove(filename)
        print('Deleted old artifacts')

        tmpdir = os.path.join(os.curdir,'tmp')
        os.mkdir(tmpdir)
        os.chdir(tmpdir)

        run_cmd(cmds['unpack'], src)
        pkg = edit_manifest('')
        run_cmd(cmds['repack'],apk_in+'_tmp.apk')
        run_cmd(cmds['sign'],apk_in+'_tmp.apk')
        run_cmd(cmds['zip'], apk_in+'_tmp.apk', apk_path+'/'+apk_in+'_intercept.apk')
        print(f'Finished reverse engineering {pkg}!')
    except Exception as e:
        print('Exception {}'.format(e))




