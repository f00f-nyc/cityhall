from django.views import generic


# Create your views here.
class CityHallViewer(generic.TemplateView):
    template_name = "viewer.html"

    def get_context_data(self, **kwargs):
        context = super(CityHallViewer, self).get_context_data(**kwargs)
        context['cityhall_url'] = "http://{}/api/".\
            format(self.request.META['HTTP_HOST'])
        return context
