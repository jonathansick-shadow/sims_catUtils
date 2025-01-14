import numpy
import ctypes
import math
import palpy as pal
import lsst.afw.geom as afwGeom
from lsst.afw.cameraGeom import PUPIL, PIXELS, FOCAL_PLANE
from lsst.afw.cameraGeom import SCIENCE
from lsst.sims.catalogs.measures.instance import compound, cached
from lsst.sims.utils import haversine, arcsecFromRadians, radiansFromArcsec, \
                            _galacticFromEquatorial, sphericalFromCartesian, \
                            cartesianFromSpherical

from lsst.sims.utils import _appGeoFromICRS, _observedFromAppGeo, _applyProperMotion
from lsst.sims.utils import _observedFromICRS, _pupilCoordsFromRaDec
from lsst.sims.utils import sphericalFromCartesian, cartesianFromSpherical
from lsst.sims.utils import rotationMatrixFromVectors
from lsst.sims.coordUtils.CameraUtils import chipNameFromPupilCoords, pixelCoordsFromPupilCoords
from lsst.sims.coordUtils.CameraUtils import focalPlaneCoordsFromPupilCoords

__all__ = ["AstrometryBase", "AstrometryStars", "AstrometryGalaxies", "AstrometrySSM",
           "PhoSimAstrometryBase", "PhoSimAstrometryStars", "PhoSimAstrometryGalaxies",
           "PhoSimAstrometrySSM",
           "CameraCoords"]

class AstrometryBase(object):
    """Collection of astrometry routines that operate on numpy arrays"""

    @compound('glon','glat')
    def get_galactic_coords(self):
        """
        Getter for galactic coordinates, in case the catalog class does not provide that

        Reads in the ra and dec from the data base and returns columns with galactic
        longitude and latitude.

        All angles are in radians
        """
        ra=self.column_by_name('raJ2000')
        dec=self.column_by_name('decJ2000')

        glon, glat = _galacticFromEquatorial(ra,dec)

        return numpy.array([glon,glat])


    @compound('x_pupil','y_pupil')
    def get_pupilFromSky(self):
        """
        Take an input RA and dec from the sky and convert it to coordinates
        in the pupil.
        """

        # these coordinates will be the mean RA, Dec from the catalog
        # with proper motion applied
        raObj = self.column_by_name('raICRS')
        decObj = self.column_by_name('decICRS')

        return _pupilCoordsFromRaDec(raObj, decObj, epoch=self.db_obj.epoch,
                                            obs_metadata=self.obs_metadata)


class CameraCoords(AstrometryBase):
    """Methods for getting coordinates from the camera object"""
    camera = None
    allow_multiple_chips = False #this is a flag which, if true, would allow
                                 #chipNameFromPupilCoords to return objects that land on
                                 #multiple chips; only the first chip would be
                                 #written to the catalog



    def get_chipName(self):
        """Get the chip name if there is one for each catalog entry"""
        xPupil, yPupil = (self.column_by_name('x_pupil'), self.column_by_name('y_pupil'))
        return chipNameFromPupilCoords(xPupil, yPupil, camera=self.camera,
                                       allow_multiple_chips=self.allow_multiple_chips)

    @compound('xPix', 'yPix')
    def get_pixelCoordinates(self):
        """Get the pixel positions (or nan if not on a chip) for all objects in the catalog"""
        if not self.camera:
            raise RuntimeError("No camera defined.  Cannot calculate pixel coordinates")
        chipNames = self.column_by_name('chipName')
        xPupil, yPupil = (self.column_by_name('x_pupil'), self.column_by_name('y_pupil'))

        return pixelCoordsFromPupilCoords(xPupil, yPupil, chipNames=chipNames,
                                          camera=self.camera)

    @compound('xFocalPlane', 'yFocalPlane')
    def get_focalPlaneCoordinates(self):
        """Get the focal plane coordinates for all objects in the catalog."""
        xPupil, yPupil = (self.column_by_name('x_pupil'), self.column_by_name('y_pupil'))

        return focalPlaneCoordsFromPupilCoords(xPupil, yPupil, camera=self.camera)

class AstrometryGalaxies(AstrometryBase):
    """
    This mixin contains astrometry getters for objects with zero parallax, proper motion, or radial
    velocity (i.e. extragalactic sources).

    Available getters are:
    raICRS, decICRS -- the RA, Dec of the object in the International Celestial Reference System

    raObserved, decObserved -- the result of applying precession, nutation, aberration, and refraction
    to raICRS, decICRS
    """

    @compound('raICRS', 'decICRS')
    def get_icrsCoordinates(self):
        """Getter for RA, Dec in the International Celestial Reference System with effects
        due to proper motion and radial velocity applied"""
        return numpy.array([self.column_by_name('raJ2000'), self.column_by_name('decJ2000')])


    @compound('raObserved','decObserved')
    def get_observedCoordinates(self):
        """Getter for observed RA, Dec (i.e. RA and Dec with all effects due to the motion
        of the Earth and refraction by the atmosphere applied)"""
        ra = self.column_by_name('raJ2000')
        dec = self.column_by_name('decJ2000')
        return _observedFromICRS(ra, dec, obs_metadata=self.obs_metadata, epoch=self.db_obj.epoch)


class AstrometryStars(AstrometryBase):
    """
    This mixin contains getters for objects with non-zero parallax, proper motion, and radial
    velocities (i.e. sources in the Milky Way).

    Available getters are:
    raICRS, decICRS -- the RA, Dec of the object in the International Celestial Reference System
    with proper motion and radial velocity applied

    raObserved, decObserved -- the result of applying precession, nutation, aberration, parallax,
    and refraction to raICRS, decICRS
    """

    def observedStellarCoordinates(self, includeRefraction = True):
        """
        Getter which converts mean coordinates in the International Celestial
        Reference Frame to observed coordinates.
        """

        #TODO
        #are we going to store proper motion in raw radians per year
        #or in sky motion = cos(dec) * (radians per year)
        #PAL asks for radians per year inputs

        pr = self.column_by_name('properMotionRa') #in radians per year
        pd = self.column_by_name('properMotionDec') #in radians per year
        px = self.column_by_name('parallax') #in radians
        rv = self.column_by_name('radialVelocity') #in km/s; positive if receding
        ra = self.column_by_name('raJ2000')
        dec = self.column_by_name('decJ2000')

        return _observedFromICRS(ra, dec, pm_ra = pr, pm_dec = pd, parallax = px, v_rad = rv,
                     includeRefraction = includeRefraction, obs_metadata=self.obs_metadata,
                     epoch=self.db_obj.epoch)


    @compound('raObserved','decObserved')
    def get_observedCoordinates(self):
        """Getter for observed RA, Dec (i.e. RA and Dec with all effects due to the motion
        of the Earth and refraction by the atmosphere applied)"""
        return self.observedStellarCoordinates()

    @compound('raICRS', 'decICRS')
    def get_icrsCoordinates(self):
        """Getter for RA, Dec in the International Celestial Reference System with effects
        due to proper motion and radial velocity applied"""
        ra0 = self.column_by_name('raJ2000')
        dec0 = self.column_by_name('decJ2000')
        pr = self.column_by_name('properMotionRa') #in radians per year
        pd = self.column_by_name('properMotionDec') #in radians per year
        px = self.column_by_name('parallax') #in radians
        rv = self.column_by_name('radialVelocity') #in km/s; positive if receding

        ra_corr, dec_corr = _applyProperMotion(ra0, dec0, pr, pd, px, rv, mjd=self.obs_metadata.mjd)
        return numpy.array([ra_corr, dec_corr])


class AstrometrySSM(AstrometryBase):
    """
    This mixin will provide getters for astrometric columns customized to Solar System Object tables
    """

    @compound('raICRS', 'decICRS')
    def get_icrsCoordinates(self):
        return numpy.array([self.column_by_name('raJ2000'), self.column_by_name('decJ2000')])


    def observedSSMCoordinates(self, includeRefraction = True):
        """
        Reads in ICRS coordinates from the database.  Returns observed coordinates
        with refraction toggled on or off based on the input boolean includeRefraction
        """
        ra = self.column_by_name('raJ2000') # in radians
        dec = self.column_by_name('decJ2000') # in radians

        return _observedFromICRS(ra, dec, includeRefraction=includeRefraction,
                                 obs_metadata=self.obs_metadata, epoch=self.db_obj.epoch)


    @compound('raObserved', 'decObserved')
    def get_observedCoordinates(self):
        return self.observedSSMCoordinates(includeRefraction = True)

    @cached
    def get_skyVelocity(self):
        """
        Gets the skyVelocity in radians per day
        """

        dradt = self.column_by_name('velRa') # in radians per day (actual sky velocity;
                                             # i.e., no need to divide by cos(dec))

        ddecdt = self.column_by_name('velDec') # in radians per day

        return numpy.sqrt(numpy.power(dradt,2) + numpy.power(ddecdt,2))


class PhoSimAstrometryBase(object):
    """
    This mixin contains the _dePrecess method necessary to create PhoSim
    images that are astrometrically consistent with their input catalogs.
    """

    def _dePrecess(self, ra_in, dec_in, obs_metadata):
        """
        Transform a set of RA, Dec pairs by subtracting out a rotation
        which represents the effects of precession, nutation, and aberration.

        Specifically:

        Calculate the displacement between the boresite and the boresite
        corrected for precession, nutation, and aberration (not refraction).

        Convert boresite and corrected boresite to Cartesian coordinates.

        Calculate the rotation matrix to go between those Cartesian vectors.

        Convert [ra_in, dec_in] into Cartesian coordinates.

        Apply the rotation vector to those Cartesian coordinates.

        Convert back to ra, dec-like coordinates

        @param [in] ra_in is a numpy array of RA in radians

        @param [in] dec_in is a numpy array of Dec in radians

        @param [in] obs_metadata is an ObservationMetaData

        @param [out] ra_out is a numpy array of de-precessed RA in radians

        @param [out] dec_out is a numpy array of de-precessed Dec in radians
        """

        if len(ra_in)==0:
            return numpy.array([[],[]])

        xyz_bore = cartesianFromSpherical(numpy.array([obs_metadata._pointingRA]),
                                          numpy.array([obs_metadata._pointingDec]))

        precessedRA, precessedDec = _observedFromICRS(numpy.array([obs_metadata._pointingRA]),
                                                      numpy.array([obs_metadata._pointingDec]),
                                                      obs_metadata=obs_metadata, epoch=2000.0,
                                                      includeRefraction=False)

        xyz_precessed = cartesianFromSpherical(precessedRA, precessedDec)

        rotMat = rotationMatrixFromVectors(xyz_precessed[0], xyz_bore[0])

        xyz_list = cartesianFromSpherical(ra_in, dec_in)

        xyz_de_precessed = numpy.array([numpy.dot(rotMat, xx) for xx in xyz_list])
        ra_deprecessed, dec_deprecessed = sphericalFromCartesian(xyz_de_precessed)
        return numpy.array([ra_deprecessed, dec_deprecessed])


class PhoSimAstrometryStars(AstrometryStars, PhoSimAstrometryBase):
    """
    This mixin contains the getter method that calculates raPhoSim,
    decPhoSim (the coordinates necessary for a PhoSim-readable
    InstanceCatalog) in the case of stellar sources.
    """

    @compound('raPhoSim','decPhoSim')
    def get_phoSimCoordinates(self):
        """Getter for RA, Dec coordinates expected by PhoSim.

        These are observed RA, Dec coordinates with the effects of nutation, aberration,
        and precession subtracted out by the PhosimInputBase._dePrecess() method.
        This preserves the relative effects of nutation, aberration, and precession while
        re-aligning the catalog with the boresite RA, Dec so that astrometric solutions
        make sense."""

        raObs, decObs = self.observedStellarCoordinates(includeRefraction = False)
        return self._dePrecess(raObs, decObs, self.obs_metadata)


class PhoSimAstrometryGalaxies(AstrometryGalaxies, PhoSimAstrometryBase):
    """
    This mixin contains the getter method that calculates raPhoSim,
    decPhoSim (the coordinates necessary for a PhoSim-readable
    InstanceCatalog) in the case of extra-galactic sources.
    """

    @compound('raPhoSim','decPhoSim')
    def get_phoSimCoordinates(self):
        """Getter for RA, Dec coordinates expected by PhoSim.

        These are observed RA, Dec coordinates with the effects of nutation, aberration,
        and precession subtracted out by the PhosimInputBase._dePrecess() method.
        This preserves the relative effects of nutation, aberration, and precession while
        re-aligning the catalog with the boresite RA, Dec so that astrometric solutions
        make sense."""

        ra = self.column_by_name('raJ2000')
        dec = self.column_by_name('decJ2000')
        raObs, decObs = _observedFromICRS(ra, dec, includeRefraction = False, obs_metadata=self.obs_metadata,
                                          epoch=self.db_obj.epoch)

        return self._dePrecess(raObs, decObs, self.obs_metadata)


class PhoSimAstrometrySSM(AstrometrySSM, PhoSimAstrometryBase):
    """
    This mixin contains the getter method that calculates raPhoSim,
    decPhoSim (the coordinates necessary for a PhoSim-readable
    InstanceCatalog) in the case of solar system sources.
    """

    @compound('raPhoSim', 'decPhoSim')
    def get_phoSimCoordinates(self):
        raObs, decObs = self.observedSSMCoordinates(includeRefraction = False)
        return self._dePrecess(raObs, decObs, self.obs_metadata)
