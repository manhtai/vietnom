import shutil as sh
import json
import os
from time import sleep

from app import db
from app.models import Nom

#############################################################################
# To UCN
#############################################################################

def to_ucn(character):
        ucn = character.encode('unicode_escape').decode('latin1')
        ucn = ucn.replace('\\', '').strip()
        if len(ucn) > int(4):
            ucn = ucn.lstrip("0")
        return ucn

#############################################################################
# SAVE TO POSTGRESQL DB
#############################################################################

# basedir = os.path.abspath(os.path.dirname(__file__))
# jsonfile = os.path.join(basedir, '2708.json')

jsonfile = '/app/app/ext/json_sql/2708.json'
with open(jsonfile, 'r') as f:
    vietnom = json.load(f)

def init_db():
    for i in vietnom:
        n = vietnom[i]
        char = n['character']
        mean = n['meaning']
        key = n['keyword']
        nom = Nom.query.filter_by(character=char).first()
        if nom is None:
            nom = Nom(id=int(i),
                      character=char,
                      meaning=mean,
                      keyword=key)
            db.session.add(nom)
            print('Add no.{}'.format(i))
            sleep(1)
        elif nom.character != char:
            nom.character = char
            nom.meaning = mean
            nom.keyword = key
            db.session.add(nom)
            print('Fix no.{}'.format(i))
            sleep(1)
    db.session.commit()

#############################################################################
# IMPORT SVG
#############################################################################

def import_svg():
    SVG="/data/repos/hochanh/rtk/kanjivg"
    VIN="/data/repos/projects/vietnom/app/static/svg"
    for i in vietnom:
        n = vietnom[i]
        char = n['character']
        char_ucn = to_ucn(char)
        suff = '0'+char_ucn[1:]+'.svg'
        suff = suff.lower()
        file_name = os.path.join(SVG,suff)
        assert os.path.isfile(file_name)
        sh.copy2(file_name, VIN)

