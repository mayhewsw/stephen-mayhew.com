from django.shortcuts import render

from langsim import langsim
from langsim import phoible

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

print "Loading phoible langs now..."
langs = phoible.loadlangs()

class LangForm(forms.Form):
        language = forms.ChoiceField(label=u'Target Language', choices=[], widget=forms.Select(), required=True)
        #only_hr = forms.BooleanField(label=u'See only High Resource Languages', initial=True, widget=forms.CheckboxInput(attrs={'disabled': False}), required=True)
        #scripts = forms.BooleanField(label=u'Take script distance into account', initial=True, widget=forms.CheckboxInput(), required=True)
        #use_wals = forms.BooleanField(label=u'Use WALS features in ranking', initial=True, widget=forms.CheckboxInput(), required=True)
        
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

                
# def showlangsim_wals(request):
#
#         #langs = filter(lambda f: f.nonzerofrac > 0.0, wals.loadLangs(fname))
#         langs = wals.loadLangs(wals_file)
#         langoptions = map(lambda p: (p["iso_code"],p["Name"]), langs)
#
#
#         form = LangForm(lang=langoptions, action="/langsim/wals")
#
#         if request.method == 'GET' and 'language' in request.GET:
#                 lang = request.GET['language']
#                 only_hr = True if "only_hr" in request.GET else False
#                 #only_hr = True if request.GET['only_hr'] == "on" else False
#                 langlist = langsim(fname, lang, 0.0, True, only_hr=only_hr, topk=100)
#                 #langlist = None
#                 msg = "Showing results for " + lang
#
#                 form.fields['language'].initial = lang
#         else:
#                 langlist = None
#                 msg = None
#                 lang = None
#
#
#         if langlist:
#                 langlist = map(lambda p: {"langname" : p[1].split(":")[0], "lang": p[1], "score":"{0:2f}".format(p[0])}, langlist)
#
#         return render(request, 'langsim.html', {'tgtlang':lang,
#                                                 'form': form,
#                                                 'langlist' : langlist,
#                                                 'msg':msg,
#                                                 'metricname' : "Distance",
#                                                 "method":"wals"})


def showlangsim_phoible(request):


        langoptions = sorted([(lang, langs[lang].name) for lang in langs], key=lambda n: n[1].lower())
        
        form = LangForm(lang=langoptions, action="/langsim")

        if request.method == 'GET' and 'language' in request.GET:
                lang = request.GET['language']
                #only_hr = True if "only_hr" in request.GET else False
                #use_wals = True if "use_wals" in request.GET else False

                langlist = langsim.sim_overall_closest(lang)
                msg = "Showing results for " + lang
                errmsg = ""

                form.fields['language'].initial = lang
        else:
                langlist = None
                msg = None
                errmsg = None
                lang = None

        def mapLL(t):
                """
                This is the format that langsim.html expects.
                """
                p = {}
                p["overall"] = t[0]
                p["phonscore"] = t[1]
                p["scriptdist"] = t[2]
                p["wals"] = t[3]
                p["langname"] = t[4].name
                p["langid"] = t[4].iso3
                
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


# def compare_wals(request):
#         fname = "/home/django/stephen-mayhew/stephen-mayhew/wals/language.csv"
#
#         featlist = None
#         msg = None
#
#         if request.method == 'GET' and 'l1' in request.GET and 'l2' in request.GET:
#                 l1 = request.GET['l1']
#                 l2 = request.GET['l2']
#                 lang1,lang2 = compareFeats(fname, l1,l2)
#                 msg = "Showing results for " + l1 + ", " + l2
#
#                 featlist = []
#                 for p in lang1.dctzip:
#                         d = {}
#                         d["name"] = p[0]
#                         d["l1"] = p[1]
#                         d["l2"] = lang2.dct[p[0]]
#                         featlist.append(d)
#
#
#         return render(request, 'compare.html', {'featlist' : featlist, 'msg':msg, 'l1':l1, 'l2':l2 })
        

def compare_phoible(request):

        msg = None
        lang1 = None
        lang2 = None
        
        if request.method == 'GET' and 'l1' in request.GET and 'l2' in request.GET:
                l1 = request.GET['l1']
                l2 = request.GET['l2']
                langs = phoible.loadlangs()
                lang1 = langs[l1]
                lang2 = langs[l2]

                lps1 = lang1.phoible_set
                lps2 = lang2.phoible_set

                msg = "Showing phonetic results for {0} and {1}".format(lang1.name,lang2.name)
                                                    
        return render(request, 'compare.html', {'featlist' : None, 'msg' : msg, 'l1':l1, 'l2':l2, 
                                                'featsets': {'common': lps1.intersection(lps2),
                                                             'l1sounds': lps1.difference(lps2),
                                                             'l2sounds': lps2.difference(lps1)} })

