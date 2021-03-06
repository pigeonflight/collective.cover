# -*- coding: utf-8 -*-
from collective.cover import _
from collective.cover.interfaces import ITileEditForm
from collective.cover.tiles.list import IListTile
from collective.cover.tiles.list import ListTile
from collective.cover.widgets.interfaces import ITextLinesSortableWidget
from collective.cover.widgets.textlinessortable import TextLinesSortableFieldWidget
from plone import api
from plone.autoform import directives as form
from plone.tiles.interfaces import ITileDataManager
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from z3c.form.converter import BaseDataConverter
from zope import schema
from zope.component import adapts
from zope.interface import implements
from zope.schema.interfaces import IDict


# autoplay feature is enabled in view mode only
INIT_JS = """$(function() {{
    Galleria.loadTheme('++resource++collective.cover/galleria-theme/galleria.cover_theme.js');
    Galleria.run('#galleria-{0}');

    var options = {{ height: 1 }};
    if ($('body').hasClass('template-view')) {{
        options.autoplay = {1};
    }}
    Galleria.configure(options);
}});
"""


class ICarouselTile(IListTile):

    """A carousel based on the Galleria JS image gallery framework."""

    autoplay = schema.Bool(
        title=_(u'Auto play'),
        required=False,
        default=True,
    )

    form.no_omit(ITileEditForm, 'uuids')
    form.widget(uuids=TextLinesSortableFieldWidget)


class CarouselTile(ListTile):

    """A carousel based on the Galleria JS image gallery framework."""

    implements(ICarouselTile)

    index = ViewPageTemplateFile('templates/carousel.pt')
    is_configurable = True
    is_editable = True
    short_name = _(u'msg_short_name_carousel', default=u'Carousel')

    def populate_with_object(self, obj):
        """Add an object to the carousel. This method will append new
        elements to the already existing list of items. If the object
        does not have an image associated, it will not be included.

        :param uuids: The list of objects' UUIDs to be used
        :type uuids: List of strings
        """
        try:
            image_size = obj.restrictedTraverse('@@images').getImageSize()
        except:
            image_size = None
        if not image_size:
            return
        super(CarouselTile, self).populate_with_object(obj)

    def autoplay(self):
        if self.data['autoplay'] is None:
            return True  # default value
        return self.data['autoplay']

    def get_title(self, item):
        """Get the title of the item, or the custom title if set.

        :param item: [required] The item for which we want the title
        :type item: Content object
        :returns: the item title
        :rtype: unicode
        """
        # First we get the title for the item itself
        title = item.Title()
        uuid = self.get_uid(item)
        data_mgr = ITileDataManager(self)
        data = data_mgr.get()
        uuids = data['uuids']
        if uuid in uuids:
            if uuids[uuid].get('custom_title', u''):
                # If we had a custom title set, then get that
                title = uuids[uuid].get('custom_title')
        return title

    def get_description(self, item):
        """Get the description of the item, or the custom description
        if set.

        :param item: [required] The item for which we want the description
        :type item: Content object
        :returns: the item description
        :rtype: unicode
        """
        # First we get the url for the item itself
        description = item.Description()
        uuid = self.get_uid(item)
        data_mgr = ITileDataManager(self)
        data = data_mgr.get()
        uuids = data['uuids']
        if uuid in uuids:
            if uuids[uuid].get('custom_description', u''):
                # If we had a custom description set, then get that
                description = uuids[uuid].get('custom_description')
        return description

    def _get_types_that_use_view_action(self):
        """Return a list of types that use the view action in listings.

        :returns: a list of content types
        :rtype: tuple
        """
        portal_properties = api.portal.get_tool('portal_properties')
        return portal_properties.site_properties.getProperty(
            'typesUseViewActionInListings', ())

    def get_url(self, item):
        """Get the URL of the item, or the custom URL if set.

        :param item: [required] The item for which we want the URL
        :type item: Content object
        :returns: the item URL
        :rtype: str
        """
        # First we get the url for the item itself
        url = item.absolute_url()
        if item.portal_type in self._get_types_that_use_view_action():
            url = url + '/view'
        uuid = self.get_uid(item)
        data_mgr = ITileDataManager(self)
        data = data_mgr.get()
        uuids = data['uuids']
        if uuid in uuids:
            if uuids[uuid].get('custom_url', u''):
                # If we had a custom url set, then get that
                url = uuids[uuid].get('custom_url')
        return url

    def init_js(self):
        if self.is_empty():
            # Galleria will display scary error messages when it
            # cannot find its <div>.  So don't start galleria unless
            # the <div> is there and has some items in it.
            return ''

        return INIT_JS.format(self.id, str(self.autoplay()).lower())


class UUIDSFieldDataConverter(BaseDataConverter):

    """A data converter using the field's ``fromUnicode()`` method."""

    adapts(IDict, ITextLinesSortableWidget)

    def toWidgetValue(self, value):
        """Convert the internal stored value into something that a
        z3c.form widget understands.

        :param value: [required] The internally stored value
        :type value: Dict
        :returns: A string with UUIDs separated by \r\n
        """

        # A new carousel tile has no items, populate_with_uids has not been
        # called yet, so incoming uuids is not an empty dict() but None
        if value is None:
            return ''

        ordered_uuids = [(k, v) for k, v in value.items()]
        ordered_uuids.sort(key=lambda x: x[1]['order'])
        return '\r\n'.join([i[0] for i in ordered_uuids])

    def toFieldValue(self, value):
        """Pass the value extracted from the widget to the internal
        structure. In this case, the value expected is already formatted.

        :param value: [required] The data extracted from the widget
        :type value: Dict
        :returns: The value to be stored in the tile
        """
        if not len(value) or not isinstance(value, dict):
            return self.field.missing_value
        return value
