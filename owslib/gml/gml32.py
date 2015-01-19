"""
An implementation of a subset of GML 3.2.

Implemented with reference to document 07-036 from
http://www.opengeospatial.org/standards/gml.

"""
"""
GML 3.3 is an extension of 3.2, with the addition of several new concepts.

Implemented with reference to document 10-129r1 from 
http://www.opengeospatial.org/standards/gml.

"""
#from __future__ import print_function
from owslib.gml import _SubclassTagTracking

namespaces = {'gml': 'http://www.opengis.net/gml/3.2',
              'gml32': 'http://www.opengis.net/gml/3.2'}


def apply_namespace(tag, namespaces):
    for key, namespace in namespaces.items():
        tag = tag.replace(key + ':', '{' + namespace + '}')
    return tag

def de_namespace(tag, namespaces):
    """Remove any fully expanded URL into the namespaced form."""
    for key, namespace in namespaces.items():
        tag = tag.replace('{' + namespace + '}', key + ':')
    return tag


def non_instantiable(cls):
    def __init__(self, *args, **kwargs):
        raise ValueError('The {} class cannot be created - it is a simple '
                         'XML container.'.format(self.__class__.__name__))
    cls.__init__ = __init__
    return cls


SRSInformationGroup_Attrs = ('axisLabels', 'uomLabels')
SRSReferenceGroup_Attrs = ('srsName', 'srsDimension') + SRSInformationGroup_Attrs


class FailedToFindOne(ValueError):
    """Raised when exactly one element was supposed to be found."""


class GMLAbstractObject(object):
    pass


class GMLAbstractGML(GMLAbstractObject):
    __metaclass__ = _SubclassTagTracking

    #: The GML tags where this GML concept can be found.
    TAGS = []
    #: The possible tags that this GML concept could contain.
    ATTRS = ('gml:id', )

    def __init__(self, attrs):
        super(GMLAbstractObject, self).__init__()
        self.attrs = attrs

    @classmethod
    def init_kwargs_from_xml(cls, element, profiles):
        attrs = {}
        kwargs = {'attrs': attrs}

        for attr_name in cls.ATTRS:
            for profile in profiles:
                attr = element.get(apply_namespace(attr_name, profile.namespaces))
                if attr is not None:
                    attrs[attr_name] = attr
                    # We're done with this attribute. Move on to the next.
                    break
        return kwargs

    @classmethod
    def construct_many_from_xml(cls, element, profiles):
        """
        A generator of instances of classes that implement this GML type.

        """
        for tag in cls.TAGS:
            for profile in profiles:
                # Expand the tag to a fully qualified one.
                fqn = profile.expand_ns(tag)
                if fqn in profile:
                    found_elements = element.findall(fqn)
                    print 'Found {} elements when looking for {}'.format(len(found_elements), fqn)
                    for found_element in found_elements:
                        yield profile[fqn].from_xml(found_element, profiles)
                    # We're done with this tag, so don't check it with other profiles.
                    break
                raise ValueError('No profile can handle {}.'.format(tag))

    @classmethod
    def construct_one_from_xml(cls, element, profiles):
        """A single instance of a class which implements this GML type."""
        items = list(cls.construct_many_from_xml(element, profiles))
        if len(items) != 1:
            raise FailedToFindOne('Expected 1 instance of {}, got {}.'.format(cls.__name__, len(items)))
        return items[0]

    @classmethod
    def from_xml(cls, element, profiles):
        """
        Create an instance of this class given an XML element and a given GML profile.

        Typically profiles are used at the construct_*_from_xml stage, meaning that this classmethod
        will only use the profiles for passing on to nested construct_*_from_xml calls, rather than
        iterating over profiles themselves.

        """
        kwargs = cls.init_kwargs_from_xml(element, profiles)
        try:
            return cls(**kwargs)
        except TypeError:
            print cls
            print cls.init_kwargs_from_xml(element, profiles)
            print('Failed to construct a {} instance. (kwargs: {!r})'.format(cls, kwargs))
            raise

    def __repr__(self):
        return '<{} instance>'.format(self.__class__.__name__)

    @classmethod
    def find(cls, parent_element, allow_none=True):
        """Find a single XML element which can be used by this GML concept."""
        element = None
        for tag in cls.TAGS or []:
            element = parent_element.find(tag, namespaces=namespaces)
            if element is not None:
                break
        if element is None and not allow_none:
            raise ValueError('Tags {} not found.'.format(', '.join(cls.TAGS or [])))
        return element

    @classmethod
    def find_one(cls, parent_element):
        return cls.find(parent_element, allow_none=False)


class GMLAbstractGeometry(GMLAbstractGML):
    # Ref: 10.1.3.1 AbstractGeometryType

    #: The GML tags that this geometry represents.
    TAGS = None

    @classmethod
    def subclass_from_xml(cls, element, profiles):
        for profile in profiles:
            if element.tag in profile:
                geometry_class = profile[element.tag]
                return geometry_class.from_xml(element, profiles)
        raise TypeError('Unsupported tag: {}'.format(element.tag))

class GMLdomainSet(GMLAbstractGML):
    # Ref: 19.3.4 domainSet, DomainSetType
    TAGS = ['gml:domainSet']

    @classmethod
    def from_xml(cls, element, profiles):
        geometry = GMLAbstractGeometry.subclass_from_xml(element[0], profiles)
        return geometry


class GMLPoint(GMLAbstractGeometry):
    # See 10.3.1 PointType, Point
    TAGS = ['gml32:Point']
    def __init__(self, attrs, coords):
        super(GMLPoint, self).__init__(attrs)
        self.coords = coords

    @classmethod
    def init_kwargs_from_xml(cls, element, profiles):
        kwargs = super(GMLPoint, cls).init_kwargs_from_xml(element, profiles)

        try:
            coords = GMLCoordinates.construct_one_from_xml(element, profiles)
        except FailedToFindOne:
            raise NotImplementedError('gml32:pos not implemented yet. Should be very simple!')

        kwargs.update({'coords': coords})
        return kwargs

    def __repr__(self):
        return 'GMLPoint({!r}, {})'.format(self.attrs, self.coords)


class GMLCoordinates(GMLAbstractGML):
    TAGS = ['gml:coordinates']

    @classmethod
    def from_xml(cls, element, profiles):
        return [float(val) for val in element.text.split()]


class GMLGrid(GMLAbstractGeometry):
    # See 19.2.2 Grid
    TAGS = ['gml:Grid']
    def __init__(self, attrs, limits, axes, dims):
        super(GMLGrid, self).__init__(attrs)
        self.limits, self.axes, self.dims = limits, axes, dims

    @classmethod
    def init_kwargs_from_xml(cls, element, profiles):
        kwargs = super(GMLGrid, cls).init_kwargs_from_xml(element, profiles)

        # Typically an Envelope.
        limits = GMLLimits.construct_one_from_xml(element, profiles)

        axes = [axis.text for axis in element.findall('gml32:axisName', namespaces=namespaces)]
        labels = element.find('gml32:axisLabels', namespaces=namespaces)
        if not axes and labels is not None:
            axes = labels.text.split()

        dims = int(element.get('dimension'))

        kwargs.update({'limits': limits, 'axes': axes, 'dims': dims})
        return kwargs


class GMLLimits(GMLAbstractGML):
    TAGS = ['gml:limits']

    @classmethod
    def from_xml(cls, element, profiles):
        return GMLAbstractGeometry.subclass_from_xml(element[0], profiles)


class GMLRectifiedGrid(GMLGrid):
    # See 19.2.3 RectifiedGrid
    TAGS = ['gml:RectifiedGrid']

    def __init__(self, attrs, limits, axes, dims, origin, offset_vectors):
        super(GMLRectifiedGrid, self).__init__(attrs, limits, axes, dims)
        self.origin, self.offset_vectors = origin, offset_vectors

    @classmethod
    def init_kwargs_from_xml(cls, element, profiles):
        kwargs = super(GMLRectifiedGrid, cls).init_kwargs_from_xml(element, profiles)

        origin_element = element.find('gml32:origin', namespaces=namespaces)[0]
        origin = GMLAbstractGeometry.subclass_from_xml(origin_element, profiles)

        offset_vectors = [GMLVector.from_xml(vector, profiles)
                          for vector in element.findall('gml32:offsetVector', namespaces=namespaces)]

        kwargs.update({'offset_vectors': offset_vectors, 'origin': origin})
        return kwargs


class AbstractReferenceableGrid(GMLGrid):
    # See 10.3 AbstractReferenceableGrid
    pass


class GMLSequenceRule(GMLAbstractGML):
    TAGS = ['gml:sequenceRule', 'gmlrgrid:sequenceRule']


class GMLEnvelope(GMLAbstractGML):
    # See 10.1.4.6 EnvelopeType, Envelope
    TAGS = ['gml:Envelope']
    ATTRS = GMLAbstractGML.ATTRS + SRSReferenceGroup_Attrs

    def __init__(self, attrs, lows, highs):
        super(GMLEnvelope, self).__init__(attrs)
        self.lows, self.highs = lows, highs

    @classmethod
    def init_kwargs_from_xml(cls, element, profiles):
        kwargs = super(GMLEnvelope, cls).init_kwargs_from_xml(element, profiles)

        lows = element.find('gml32:lowerCorner', namespaces=namespaces).text.split()
        highs = element.find('gml32:upperCorner', namespaces=namespaces).text.split()
        lows = map(float, lows)
        highs = map(float, highs)

        kwargs.update({'lows': lows, 'highs': highs})
        return kwargs

    def __repr__(self):
        return 'GMLEnvelope({!r}, lows={}, highs={})'.format(self.attrs, self.lows, self.highs)


class GMLGridEnvelope(GMLAbstractGML):
    # See 10.1.4.6 EnvelopeType, Envelope
    TAGS = ['gml:GridEnvelope']

    def __init__(self, attrs, lows, highs):
        super(GMLGridEnvelope, self).__init__(attrs)
        self.lows, self.highs = lows, highs

    @classmethod
    def init_kwargs_from_xml(cls, element, profiles):
        kwargs = super(GMLGridEnvelope, cls).init_kwargs_from_xml(element, profiles)

        # Note: This is not always 2 dimensional!
        lows = element.find('gml32:low', namespaces=namespaces).text.split()
        highs = element.find('gml32:high', namespaces=namespaces).text.split()

        kwargs.update({'lows': map(int, lows), 'highs': map(int, highs)})
        return kwargs

    def __repr__(self):
        return 'GMLGridEnvelope({!r}, lows={}, highs={})'.format(self.attrs, self.lows, self.highs)



class GMLVector(GMLAbstractGML):
    # See 10.1.4.5 VectorType, Vector
    def __init__(self, attrs, components):
        super(GMLVector, self).__init__(attrs)
        self.components = components

    @classmethod
    def init_kwargs_from_xml(cls, element, profiles):
        kwargs = super(GMLVector, cls).init_kwargs_from_xml(element, profiles)

        components = [float(val) for val in element.text.split()]

        kwargs.update({'components': components})
        return kwargs

    def __repr__(self):
        return 'GMLVector({!r}, {})'.format(self.attrs, self.components)


class GMLPosList(GMLAbstractGML):
    # See 10.1.4.2 DirectPositionListType, posList
    TAGS = ['gml32:posList']

    @classmethod
    def from_xml(cls, element, profiles):
        values = map(float, element.text.split())
        return values

# Chapter 14

GMLTimeFormat = '%Y-%m-%dT%H:%M:%SZ'


class GMLTimePosition(GMLAbstractGML):
    # See 14.2.2.7 TimePositionType, timePosition
    def __init__(self, attrs, datetime):
        super(GMLTimePosition, self).__init__(attrs)
        self.datetime = datetime

    @classmethod
    def init_kwargs_from_xml(cls, element, profiles):
        kwargs = super(GMLTimePosition, cls).init_kwargs_from_xml(element, profiles)

        from datetime import datetime
        dt = datetime.strptime(element.text, GMLTimeFormat)

        kwargs.update({'datetime': dt})
        return kwargs

    def __repr__(self):
        return 'GMLTimePosition({!r}, {!r})'.format(self.attrs, self.datetime)


class GMLTimePeriod(GMLAbstractGML):
    # 14.2.2.5 TimePeriod
    def __init__(self, attrs, start, end):
        super(GMLTimePeriod, self).__init__(attrs)
        self.start = start
        self.end = end

    @classmethod
    def init_kwargs_from_xml(cls, element, profiles):
        kwargs = super(GMLTimePeriod, cls).init_kwargs_from_xml(element, profiles)

        start = element.find('gml32:beginPosition', namespaces=namespaces)
        if start is None:
            raise ValueError('End position not found. gml32:start needs to be implemented.')
#            start = element.find('gml32:begin', namespaces=namespaces)

        end = element.find('gml32:endPosition', namespaces=namespaces)
        if end is None:
            raise ValueError('End position not found. gml32:end needs to be implemented.')
#            end = element.find('gml32:end', namespaces=namespaces)

        from datetime import datetime
        start = datetime.strptime(start.text, GMLTimeFormat)
        end = datetime.strptime(end.text, GMLTimeFormat)

        kwargs.update({'start': start, 'end': end})
        return kwargs

    def __repr__(self):
        return 'TimePeriod({!r}, {!r}, {!r})'.format(self.attrs, self.start, self.end)

# Chapter 19

class GMLRangeSet(GMLAbstractGML):
    # See 19.3.5 rangeSet, RangeSetType
    def __init__(self, attrs, data):
        super(GMLRangeSet, self).__init__(attrs)
        self.data = data

    @classmethod
    def init_kwargs_from_xml(cls, element, profiles):
        kwargs = super(GMLRangeSet, cls).init_kwargs_from_xml(element, profiles)

        data = GMLDataBlock.from_xml(element.find('gml32:DataBlock', namespaces=namespaces), profiles)
        parameters = element.find('gml32:rangeParameters', namespaces=namespaces)
        if parameters is not None:
            raise NotImplementedError('Range parameters not yet implemented in gml32:RangeSet.')

        kwargs.update({'data': data})
        return kwargs


class GMLDataBlock(GMLAbstractGML):
    # See 19.3.6 DataBlock
    def __init__(self, attrs, values):
        super(GMLDataBlock, self).__init__(attrs)
        self.values = values

    @classmethod
    def init_kwargs_from_xml(cls, element, profiles):
        kwargs = super(GMLDataBlock, cls).init_kwargs_from_xml(element, profiles)

        values = GMLtupleList.construct_one_from_xml(element, profiles)

        kwargs.update({'values': values})
        return kwargs


class GMLtupleList(GMLAbstractGML):
    TAGS = ['gml:tupleList']

    @classmethod
    def from_xml(cls, element, profiles):
        components = element.text.split(',')
        return tuple(component.split() for component in components)


class Profile(dict):
    def __init__(self, tags, namespaces):
        self.namespaces = namespaces
        dict.__init__(self, tags)

    def copy(self):
        return self.__class__(super(Profile, self).copy(), self.namespaces)

    def expand_ns(self, tag):
        """
        Convert a tag such as "abc:Testing" to "{abcdefg}Testing" provided a
        namespace such as "abc": "abcdefg" exists in this profile.

        """
        for key, namespace in self.namespaces.items():
            tag = tag.replace(key + ':', '{' + namespace + '}')
        return tag

    def contract_ns(self, tag):
        """
        Convert a tag such as "{abcdefg}Testing" to "abc:Testing" provided a
        namespace such as "abc": "abcdefg" exists in this profile.

        """
        for key, namespace in self.namespaces.items():
            tag = tag.replace('{' + namespace + '}', key + ':')
        return tag

# Maps the tag to the class which implements it.
gml32_profile = {'gml:Point': GMLPoint,
                 'gml:posList': GMLPosList,
                 'gml:RectifiedGrid': GMLRectifiedGrid,
                 'gml:tupleList': GMLtupleList,
                 'gml:coordinates': GMLCoordinates,
                 'gml:grid': GMLGrid,
                 'gml:RectifiedGrid': GMLRectifiedGrid,
                 'gml:sequenceRule': GMLSequenceRule,
                 'gml:Envelope': GMLEnvelope,
                 'gml:GridEnvelope': GMLGridEnvelope,
                 'gml:limits': GMLLimits,
                 }
gml32_profile = Profile({apply_namespace(tag, namespaces): value for tag, value in gml32_profile.items()},
                        namespaces)

#gml32_profile = gml32_profile.copy()
