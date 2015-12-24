from django.template import RequestContext, loader
from django.http import HttpResponse
from django.shortcuts import render

from wals.langsim import *
import wals.wals as wals
from wals.compare import *


import sys
sys.path.insert(0, '/home/django/stephen-mayhew/stephen-mayhew/phoible/python') # HAACK
import phoible

from django import forms
from django.forms import widgets

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

wals_file = "/home/django/stephen-mayhew/stephen-mayhew/wals/language.csv"

class LangForm(forms.Form):
        language = forms.ChoiceField(label=u'Target Language', choices=[], widget=forms.Select(), required=True)
        only_hr = forms.BooleanField(label=u'See only High Resource Languages', initial=True, widget=forms.CheckboxInput(attrs={'disabled': False}), required=True)
        scripts = forms.BooleanField(label=u'Take script distance into account', initial=True, widget=forms.CheckboxInput(), required=True)
        use_wals = forms.BooleanField(label=u'Use WALS features in ranking', initial=True, widget=forms.CheckboxInput(), required=True)
        
        def __init__(self, *args, **kwargs):
                lang_choices = kwargs.pop('lang')
                action = kwargs.pop('action')
                super(LangForm, self).__init__(*args, **kwargs)
                self.fields['language'].choices = lang_choices
                self.helper = FormHelper()
                self.helper.form_action = action
                self.helper.form_method = "get"
                
                self.helper.form_class = 'form-horizontal'
                self.helper.label_class = 'col-lg-2'
                self.helper.field_class = 'col-lg-8'
                
                self.helper.add_input(Submit('submit', 'Submit'))

                
def showlangsim_wals(request):

        #langs = filter(lambda f: f.nonzerofrac > 0.0, wals.loadLangs(fname))
        langs = wals.loadLangs(wals_file)
        langoptions = map(lambda p: (p["iso_code"],p["Name"]), langs)
        
        
        form = LangForm(lang=langoptions, action="/langsim/wals")
        
        if request.method == 'GET' and 'language' in request.GET:
                lang = request.GET['language']
                only_hr = True if "only_hr" in request.GET else False
                #only_hr = True if request.GET['only_hr'] == "on" else False
                langlist = langsim(fname, lang, 0.0, True, only_hr=only_hr, topk=100)
                #langlist = None
                msg = "Showing results for " + lang

                form.fields['language'].initial = lang
        else:
                langlist = None
                msg = None
                lang = None
                

        if langlist:
                langlist = map(lambda p: {"langname" : p[1].split(":")[0], "lang": p[1], "score":"{0:2f}".format(p[0])}, langlist)
        
        return render(request, 'langsim.html', {'tgtlang':lang,
                                                'form': form,
                                                'langlist' : langlist,
                                                'msg':msg,
                                                'metricname' : "Distance",
                                                "method":"wals"})


def showlangsim_phoible(request):
        fname = "/home/django/stephen-mayhew/stephen-mayhew/phoible/gold-standard/phoible-phonemes.tsv"

        langs,code2name = phoible.loadLangs(fname)

        langoptions = sorted([(lang, code2name[lang]) for lang in langs], key=lambda n: n[1].lower())
        
        form = LangForm(lang=langoptions, action="/langsim/phoible")

        if request.method == 'GET' and 'language' in request.GET:
                lang = request.GET['language']
                only_hr = True if "only_hr" in request.GET else False
                scripts = True if "scripts" in request.GET else False
                use_wals = True if "use_wals" in request.GET else False

                # list of dictionaries (sorted by phonscore), with keys phonscore, scriptdist, langid
                langlist = phoible.langsim(lang, langs,code2name, only_hr=only_hr, script_rerank=scripts)
                msg = "Showing results for " + lang
                errmsg = ""
                if use_wals:
                        # this is a list of WALSLanguage objects
                        wals_langs = wals.loadLangs(wals_file)

                        # maps ISO code to the object
                        wldct = {}
                        wl_lang = None
                        for wl in wals_langs:
                                wldct[wl["iso_code"]] = wl
                                if wl["iso_code"] == lang:
                                        wl_lang = wl

                        if wl_lang == None:
                                errmsg += "Couldn't find " + lang + " in wals_langs."
                        else:
                                # rerank langlist according to genus/family
                                # if genus the same, multiply by 1.5,
                                # if family and genus the same, multiply by 2
                                reranked = []
                                for phl in langlist:
                                        phlid = phl["langid"]

                                        if phlid not in wldct:
                                                errmsg += "WALS does not have phoible lang: {0} ({1}). ".format(code2name[phlid],phlid)
                                                phl["wals"] = 1
                                                continue
                                        currlang = wldct[phlid]

                                        # compare currlang against wl_lang
                                        multiplier = 1
                                        if currlang["genus"] == wl_lang["genus"]:
                                                multiplier = 1.5
                                                if currlang["family"] == wl_lang["family"]:
                                                        multiplier = 2
                                                        
                                        phl["wals"] = multiplier

                
                form.fields['language'].initial = lang
        else:
                langlist = None
                msg = None
                errmsg = None
                lang = None

        def mapLL(p):
                """
                This is the format that langsim.html expects.
                """
                langname = code2name[p["langid"]]

                p["langname"] = langname

                p["overall"] = p["phonscore"]
                
                if "wals" in p:
                        p["overall"] *= p["wals"]
                if "scriptdist" in p:
                        if p["scriptdist"] is None:
                                p["overall"] = 0
                        else:
                                p["overall"] *= p["scriptdist"]
                
                return p
                
        if langlist:
                langlist = map(mapLL, langlist)
                # then rerank according to score...
                langlist = sorted(langlist, key=lambda p: p["overall"], reverse=True)
                
        return render(request, 'langsim.html', {'tgtlang':lang,
                                                'form': form,
                                                'langlist' : langlist,
                                                'msg': msg,
                                                'errmsg': errmsg,
                                                'metricname' : "Overall",
                                                'method':"phoible"})


def compare_wals(request):
        fname = "/home/django/stephen-mayhew/stephen-mayhew/wals/language.csv"

        featlist = None
        msg = None
        
        if request.method == 'GET' and 'l1' in request.GET and 'l2' in request.GET:
                l1 = request.GET['l1']
                l2 = request.GET['l2']
                lang1,lang2 = compareFeats(fname, l1,l2)
                msg = "Showing results for " + l1 + ", " + l2

                featlist = []
                for p in lang1.dctzip:
                        d = {}
                        d["name"] = p[0]
                        d["l1"] = p[1]
                        d["l2"] = lang2.dct[p[0]]
                        featlist.append(d)

                
        return render(request, 'compare.html', {'featlist' : featlist, 'msg':msg, 'l1':l1, 'l2':l2 })
        

def compare_phoible(request):
        
        fname = "/home/django/stephen-mayhew/stephen-mayhew/phoible/gold-standard/phoible-phonemes.tsv"
        
        msg = None
        lang1 = None
        lang2 = None
        
        if request.method == 'GET' and 'l1' in request.GET and 'l2' in request.GET:
                l1 = request.GET['l1']
                l2 = request.GET['l2']
                langs,code2name = phoible.loadLangs(fname)
                lang1 = langs[l1]
                lang2 = langs[l2]

                msg = "Showing phonetic results for {0} and {1}".format(code2name[l1],code2name[l2])
                                                    
        return render(request, 'compare.html', {'featlist' : None, 'msg' : msg, 'l1':l1, 'l2':l2, 
                                                'featsets': {'common' : lang1.intersection(lang2),
                                                             'l1sounds' : lang1.difference(lang2),
                                                             'l2sounds' : lang2.difference(lang1)} })

