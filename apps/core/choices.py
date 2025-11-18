from django.db import models


class BuildingType(models.TextChoices):
    EFH = "efh", "Einfamilienhaus"
    MFH = "mfh", "Mehrfamilienhaus"
    COMMERCIAL = "commercial", "Gewerbe"


class GridType(models.TextChoices):
    ONE_PHASE = "1p", "1-Polig"
    THREE_PHASE = "3p", "3-Polig"
    UNKNOWN = "unknown", "Unbekannt"


class WallboxClass(models.TextChoices):
    CLASS_4KW = "4kw", "Wallbox bis 4 kW"
    CLASS_11KW = "11kw", "Wallbox 11 kW"
    CLASS_22KW = "22kw", "Wallbox 22 kW"


class WallboxMount(models.TextChoices):
    WALL = "wall", "Wandmontage"
    STAND = "stand", "Staendermontage"


class GroundingChoice(models.TextChoices):
    YES = "yes", "Ja, vorhanden"
    NO = "no", "Nein"
    UNKNOWN = "unknown", "Unbekannt"


class FeedInMode(models.TextChoices):
    SURPLUS = "surplus", "Ueberschusseinspeisung"
    FULL = "full", "Volleinspeisung"
    MIXED = "mixed", "Gemischt"


class InverterLocation(models.TextChoices):
    BASEMENT = "basement", "Keller"
    GARAGE = "garage", "Garage"
    ATTIC = "attic", "Dachboden"
    UTILITY_ROOM = "utility_room", "Hauswirtschaftsraum"
    OUTDOOR = "outdoor", "Aussenbereich (wettergeschuetzt)"
    OTHER = "other", "Anderer Ort"


class StorageLocation(models.TextChoices):
    SAME_AS_INVERTER = "same_as_inverter", "Gleicher Ort wie Wechselrichter"
    BASEMENT = "basement", "Keller"
    GARAGE = "garage", "Garage"
    ATTIC = "attic", "Dachboden"
    UTILITY_ROOM = "utility_room", "Hauswirtschaftsraum"
    OUTDOOR = "outdoor", "Aussenbereich (wettergeschuetzt)"
    OTHER = "other", "Anderer Ort"
