
class _SubclassTagTracking(type):
    """A metaclass to keep track of all TAGS of itself and subclasses."""
    def __init__(cls, name, bases, dct):
        # Update the _geometry_types dictionary for any subclass which
        # is created.
        cls._SUBCLASS_TAGS = set(cls.TAGS or [])
        if cls.TAGS:
            for base in bases:
                super_tags = getattr(base, '_SUBCLASS_TAGS', None)
                if super_tags is not None:
                    super_tags.update(cls.TAGS)

        super(_SubclassTagTracking, cls).__init__(name, bases, dct)
