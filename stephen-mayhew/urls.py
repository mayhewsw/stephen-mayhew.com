from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView
from django.contrib import admin
import views

admin.autodiscover()

urlpatterns = patterns('',
                       
                       url(r'^$', TemplateView.as_view(template_name='index.html')),
                       url(r'^langsim$', TemplateView.as_view(template_name='choose.html')),

                       url(r'^langsim/phoible$', views.showlangsim_phoible),
                       url(r'^compare/phoible$', views.compare_phoible),
                       
                       url(r'^admin/', include(admin.site.urls)),
)
