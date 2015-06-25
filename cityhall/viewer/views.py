# Copyright 2015 Digital Borderlands Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from django.views import generic


# Create your views here.
class CityHallViewer(generic.TemplateView):
    template_name = "viewer.html"

    def get_context_data(self, **kwargs):
        context = super(CityHallViewer, self).get_context_data(**kwargs)
        context['cityhall_url'] = "http://{}/api/".\
            format(self.request.META['HTTP_HOST'])
        return context
