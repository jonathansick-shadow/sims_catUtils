"""
This file defines some test catalog and DBObject classes for use with unit tests.

To date (30 October 2014) testPhotometryMixins.py and testCosmologyMixins.py import from this module
"""

import numpy
import os
import sqlite3
import json
from lsst.utils import getPackageDir
from lsst.sims.catalogs.measures.instance import InstanceCatalog, register_method, register_class, compound
from lsst.sims.catUtils.mixins import AstrometryStars, AstrometryGalaxies
from lsst.sims.photUtils.SignalToNoise import calcSkyCountsPerPixelForM5
from lsst.sims.photUtils import BandpassDict, SedList
from lsst.sims.catUtils.mixins import PhotometryGalaxies, PhotometryStars, Variability, \
    VariabilityStars, VariabilityGalaxies, EBVmixin

__all__ = ["makeStarDatabase", "makeGalaxyDatabase",
           "TestVariabilityMixin", "testDefaults", "cartoonPhotometryStars",
           "cartoonPhotometryGalaxies", "testCatalog", "cartoonStars",
           "cartoonStarsOnlyI", "cartoonStarsIZ",
           "cartoonGalaxies", "cartoonGalaxiesIG", "testStars", "testGalaxies",
           "galaxiesWithHoles"]


def makeStarDatabase(filename='StellarPhotometryDB.db', size=1000, seedVal=32,
                     radius=1.0, pointingRA=50.0, pointingDec=-10.0):

    star_seds = ['km20_5750.fits_g40_5790', 'm2.0Full.dat', 'bergeron_6500_85.dat_6700']

    # Now begin building the database.
    # First create the tables.
    conn = sqlite3.connect(filename)
    c = conn.cursor()

    numpy.random.seed(seedVal)

    rr = numpy.random.sample(size)*radius
    theta = numpy.random.sample(size)*2.0*numpy.pi

    try:
        c.execute('''CREATE TABLE StarAllForceseek
                  (simobjid int, ra real, decl real, magNorm real,
                  mudecl real, mura real, ebv real, vrad real, varParamStar text, sedFilename text, parallax real)''')
    except:
        raise RuntimeError("Error creating StarAllForceseek table.")

    magnormStar = numpy.random.sample(size)*5.0+17.0
    magnormStar = numpy.random.sample(size)*4.0 + 17.0
    mudecl = numpy.random.sample(size)*0.0001
    mura = numpy.random.sample(size)*0.0001
    ebv = numpy.random.sample(size)*0.05
    vrad = numpy.random.sample(size)*1.0
    parallax = 0.00045+numpy.random.sample(size)*0.00001

    for i in range(size):
        raStar = pointingRA + rr[i]*numpy.cos(theta[i])
        decStar = pointingDec + rr[i]*numpy.sin(theta[i])

        cmd = '''INSERT INTO StarAllForceseek VALUES (%i, %f, %f, %f, %f, %f, %f, %f, %s, '%s', %f)''' %\
            (i, raStar, decStar, magnormStar[i], mudecl[i], mura[i],
             ebv[i], vrad[i], 'NULL', star_seds[i%len(star_seds)], parallax[i])

        c.execute(cmd)

    conn.commit()
    conn.close()


def makeGalaxyDatabase(filename='GalaxyPhotometryDB.db', size=1000, seedVal=32,
                       radius=1.0, pointingRA=50.0, pointingDec=-10.0):

    galaxy_seds = ['Const.80E07.02Z.spec', 'Inst.80E07.002Z.spec', 'Burst.19E07.0005Z.spec']
    agn_sed = 'agn.spec'

    # Now begin building the database.
    # First create the tables.
    conn = sqlite3.connect(filename)
    c = conn.cursor()

    try:
        c.execute('''CREATE TABLE galaxy
                     (galtileid int, galid int, ra real, dec real,
                      bra real, bdec real, dra real, ddec real,
                      agnra real, agndec real,
                      magnorm_bulge, magnorm_disk, magnorm_agn,
                      sedname_bulge text, sedname_disk text, sedname_agn text,
                      varParamStr text,
                      a_b real, b_b real, pa_bulge real, bulge_n int,
                      a_d real, b_d real, pa_disk real, disk_n int,
                      ext_model_b text, av_b real, rv_b real,
                      ext_model_d text, av_d real, rv_d real,
                      u_ab real, g_ab real, r_ab real, i_ab real,
                      z_ab real, y_ab real,
                      redshift real, BulgeHalfLightRadius real, DiskHalfLightRadius real)''')

        conn.commit()
    except:
        raise RuntimeError("Error creating galaxy table.")

    mjd = 52000.0

    numpy.random.seed(seedVal)

    rr = numpy.random.sample(size)*radius
    theta = numpy.random.sample(size)*2.0*numpy.pi

    ra = pointingRA + rr*numpy.cos(theta)
    dec = pointingDec + rr*numpy.sin(theta)

    bra = numpy.radians(ra+numpy.random.sample(size)*0.01*radius)
    bdec = numpy.radians(dec+numpy.random.sample(size)*0.01*radius)
    dra = numpy.radians(ra + numpy.random.sample(size)*0.01*radius)
    ddec = numpy.radians(dec + numpy.random.sample(size)*0.01*radius)
    agnra = numpy.radians(ra + numpy.random.sample(size)*0.01*radius)
    agndec = numpy.radians(dec + numpy.random.sample(size)*0.01*radius)

    magnorm_bulge = numpy.random.sample(size)*4.0 + 17.0
    magnorm_disk = numpy.random.sample(size)*5.0 + 17.0
    magnorm_agn = numpy.random.sample(size)*5.0 + 17.0
    b_b = numpy.random.sample(size)*0.2
    a_b = b_b+numpy.random.sample(size)*0.05
    b_d = numpy.random.sample(size)*0.5
    a_d = b_d+numpy.random.sample(size)*0.1

    BulgeHalfLightRadius = numpy.random.sample(size)*0.2
    DiskHalfLightRadius = numpy.random.sample(size)*0.5

    pa_bulge = numpy.random.sample(size)*360.0
    pa_disk = numpy.random.sample(size)*360.0

    av_b = numpy.random.sample(size)*0.4
    av_d = numpy.random.sample(size)*0.4
    rv_b = numpy.random.sample(size)*0.1 + 3.0
    rv_d = numpy.random.sample(size)*0.1 + 3.0

    u_ab = numpy.random.sample(size)*4.0 + 17.0
    g_ab = numpy.random.sample(size)*4.0 + 17.0
    r_ab = numpy.random.sample(size)*4.0 + 17.0
    i_ab = numpy.random.sample(size)*4.0 + 17.0
    z_ab = numpy.random.sample(size)*4.0 + 17.0
    y_ab = numpy.random.sample(size)*4.0 + 17.0
    redshift = numpy.random.sample(size)*2.0

    t0_mjd = numpy.random.sample(size)*10.0+mjd
    agn_tau = numpy.random.sample(size)*1000.0 + 1000.0
    agnSeed = numpy.random.random_integers(low=2, high=4000, size=size)
    agn_sfu = numpy.random.sample(size)
    agn_sfg = numpy.random.sample(size)
    agn_sfr = numpy.random.sample(size)
    agn_sfi = numpy.random.sample(size)
    agn_sfz = numpy.random.sample(size)
    agn_sfy = numpy.random.sample(size)

    for i in range(size):
        varParam = {'varMethodName': 'applyAgn',
                    'pars': {'agn_tau': agn_tau[i], 't0_mjd': t0_mjd[i],
                             'agn_sfu': agn_sfu[i], 'agn_sfg': agn_sfg[i], 'agn_sfr': agn_sfr[i],
                             'agn_sfi': agn_sfi[i], 'agn_sfz': agn_sfz[i], 'agn_sfy': agn_sfy[i],
                             'seed': int(agnSeed[i])}}

        paramStr = json.dumps(varParam)

        cmd = '''INSERT INTO galaxy VALUES (%i, %i, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f,
                                            '%s', '%s', '%s', '%s',
                                            %f, %f, %f, %i,
                                            %f, %f, %f, %i,
                                            '%s', %f, %f,
                                            '%s', %f, %f,
                                            %f, %f, %f, %f, %f, %f,
                                            %f, %f, %f)''' %\
            (i, i, ra[i], dec[i], bra[i], bdec[i], dra[i], ddec[i], agnra[i], agndec[i],
             magnorm_bulge[i], magnorm_disk[i], magnorm_agn[i],
             galaxy_seds[(i+1)%len(galaxy_seds)], galaxy_seds[i%len(galaxy_seds)], agn_sed,
             paramStr,
             a_b[i], b_b[i], pa_bulge[i], 4,
             a_d[i], b_d[i], pa_disk[i], 1,
             'CCM', av_b[i], rv_b[i],
             'CCM', av_d[i], rv_d[i],
             u_ab[i], g_ab[i], r_ab[i], i_ab[i], z_ab[i], y_ab[i], redshift[i],
             BulgeHalfLightRadius[i], DiskHalfLightRadius[i])
        c.execute(cmd)

    conn.commit()
    conn.close()


@register_class
class TestVariabilityMixin(Variability):
    """
    This is a mixin which provides a dummy variability method for use in unit tests
    """
    @register_method('testVar')
    def applySineVar(self, varParams, expmjd):
        period = varParams['period']
        amplitude = varParams['amplitude']
        phase = expmjd%period
        magoff = amplitude*numpy.sin(2*numpy.pi*phase)
        return {'u': magoff, 'g': magoff, 'r': magoff, 'i': magoff, 'z': magoff, 'y': magoff}


class testDefaults(object):
    """
    This class just provides default values for quantities that
    the astrometry mixins require in order to run
    """

    def get_proper_motion_ra(self):
        ra = self.column_by_name('raJ2000')
        out = numpy.zeros(len(ra))
        for i in range(len(ra)):
            out[i] = 0.0

        return out

    def get_proper_motion_dec(self):
        ra = self.column_by_name('raJ2000')
        out = numpy.zeros(len(ra))
        for i in range(len(ra)):
            out[i] = 0.0

        return out

    def get_parallax(self):
        ra = self.column_by_name('raJ2000')
        out = numpy.zeros(len(ra))
        for i in range(len(ra)):
            out[i] = 1.2

        return out

    def get_radial_velocity(self):
        ra = self.column_by_name('raJ2000')
        out = numpy.zeros(len(ra))
        for i in range(len(ra)):
            out[i] = 0.0

        return out


class cartoonPhotometryStars(PhotometryStars):
    """
    This is a class to support loading cartoon bandpasses into photometry so that we can be sure
    that the photometry mixin is loading the right files and calculating the right magnitudes.

    In addition to creating a catalog, when the get_magnitude method below is called, it will
    add sedMasterList and magnitudeMasterList to the catalog instantiation.  These are lists
    containing the magnitudes output to the catalog and the SEDs used to calculate them.

    Having these variables allows the unittest to verify the output of the catalog
    (see testAlternateBandpassesStars in testPhotometry.py to see how this works)
    """

    @compound('cartoon_u', 'cartoon_g', 'cartoon_r', 'cartoon_i', 'cartoon_z')
    def get_magnitudes(self):
        """
        Example photometry getter for alternative (i.e. non-LSST) bandpasses
        """

        idNames = self.column_by_name('id')
        columnNames = [name for name in self.get_magnitudes._colnames]
        bandpassNames = ['u', 'g', 'r', 'i', 'z']
        bandpassDir = os.path.join(getPackageDir('sims_photUtils'), 'tests', 'cartoonSedTestData')

        if not hasattr(self, 'cartoonBandpassDict'):
            self.cartoonBandpassDict = BandpassDict.loadTotalBandpassesFromFiles(bandpassNames, bandpassDir = bandpassDir,
                                                                                 bandpassRoot = 'test_bandpass_')

        output = self._magnitudeGetter(self.cartoonBandpassDict, self.get_magnitudes._colnames)

        #############################################################################
        # Everything below this comment exists solely for the purposes of the unit test
        # if you need to write a customized getter for photometry that uses non-LSST
        # bandpasses, you only need to emulate the code above this comment.

        magNormList = self.column_by_name('magNorm')
        sedNames = self.column_by_name('sedFilename')
        av = self.column_by_name('galacticAv')

        # the two variables below will allow us to get at the SED and magnitude
        # data from within the unit test class, so that we can be sure
        # that the mixin loaded the correct bandpasses
        sublist = SedList(sedNames, magNormList, galacticAvList=av)

        for ss in sublist:
            self.sedMasterList.append(ss)

        if len(output) > 0:
            for i in range(len(output[0])):
                subList = []
                for j in range(len(output)):
                    subList.append(output[j][i])

                self.magnitudeMasterList.append(subList)

        return output


class cartoonPhotometryGalaxies(PhotometryGalaxies):
    """
    This is a class to support loading cartoon bandpasses into photometry so that we can be sure
    that the photometry mixin is loading the right files and calculating the right magnitudes.

    In addition to writing the catalog, when the get_magnitudes method below is called, the
    variables sedMasterDict and mangitudeMasterDict are added to the catalog instantiation.
    These store the magnitudes calculated for the catalog and the SEDs used to find them.

    This allows the unittest to verify the contents of the catalog
    (see testAlternateBandpassesGalaxies in testPhotometry.py to see how this works)
    """

    @compound('cbulge_u', 'cbulge_g', 'cbulge_r', 'cbulge_i', 'cbulge_z')
    def get_cartoon_bulge_mags(self):

        if not hasattr(self, 'cartoonBandpassDict'):
            bandpassNames = ['u', 'g', 'r', 'i', 'z']
            bandpassDir = getPackageDir('sims_photUtils')
            bandpassDir = os.path.join(bandpassDir, 'tests', 'cartoonSedTestData')

            self.cartoonBandpassDict = BandpassDict.loadTotalBandpassesFromFiles(bandpassNames,
                                                                                 bandpassDir=bandpassDir,
                                                                                 bandpassRoot = 'test_bandpass_')

        return self._magnitudeGetter('bulge', self.cartoonBandpassDict,
                                     self.get_cartoon_bulge_mags._colnames)

    @compound('cdisk_u', 'cdisk_g', 'cdisk_r', 'cdisk_i', 'cdisk_z')
    def get_cartoon_disk_mags(self):

        if not hasattr(self, 'cartoonBandpassDict'):
            bandpassNames = ['u', 'g', 'r', 'i', 'z']
            bandpassDir = getPackageDir('sims_photUtils')
            bandpassDir = os.path.join(bandpassDir, 'tests', 'cartoonSedTestData')

            self.cartoonBandpassDict = BandpassDict.loadTotalBandpassesFromFiles(bandpassNames,
                                                                                 bandpassDir=bandpassDir,
                                                                                 bandpassRoot = 'test_bandpass_')

        return self._magnitudeGetter('disk', self.cartoonBandpassDict,
                                     self.get_cartoon_disk_mags._colnames)

    @compound('cagn_u', 'cagn_g', 'cagn_r', 'cagn_i', 'cagn_z')
    def get_cartoon_agn_mags(self):

        if not hasattr(self, 'cartoonBandpassDict'):
            bandpassNames = ['u', 'g', 'r', 'i', 'z']
            bandpassDir = getPackageDir('sims_photUtils')
            bandpassDir = os.path.join(bandpassDir, 'tests', 'cartoonSedTestData')

            self.cartoonBandpassDict = BandpassDict.loadTotalBandpassesFromFiles(bandpassNames,
                                                                                 bandpassDir=bandpassDir,
                                                                                 bandpassRoot = 'test_bandpass_')

        return self._magnitudeGetter('agn', self.cartoonBandpassDict,
                                     self.get_cartoon_agn_mags._colnames)

    @compound('ctotal_u', 'ctotal_g', 'ctotal_r', 'ctotal_i', 'ctotal_z')
    def get_cartoon_total_mags(self):
        idList = self.column_by_name('uniqueId')
        numObj = len(idList)
        output = []
        for columnName in self.get_cartoon_total_mags._colnames:
            if columnName not in self._actually_calculated_columns:
                sub_list = [numpy.NaN]*numObj
            else:
                bandpass = columnName[-1]
                bulge = self.column_by_name('cbulge_%s' % bandpass)
                disk = self.column_by_name('cdisk_%s' % bandpass)
                agn = self.column_by_name('cagn_%s' % bandpass)
                sub_list = self.sum_magnitudes(bulge=bulge, disk=disk, agn=agn)

            output.append(sub_list)
        return numpy.array(output)


class testCatalog(InstanceCatalog, AstrometryStars, VariabilityStars, testDefaults):
    catalog_type = 'MISC'
    default_columns = [('expmjd', 5000.0, float)]

    def db_required_columns(self):
        return ['raJ2000'], ['varParamStr']


class cartoonStars(InstanceCatalog, AstrometryStars, EBVmixin, VariabilityStars, cartoonPhotometryStars, testDefaults):
    """
    A catalog of stars relying on the cartoon photometry methods (which use non-LSST bandpasses
    and output extra data for use by unit tests)
    """
    catalog_type = 'cartoonStars'
    column_outputs = ['id', 'raObserved', 'decObserved', 'magNorm',
                      'cartoon_u', 'cartoon_g', 'cartoon_r', 'cartoon_i', 'cartoon_z']

    # the lists below will contain the SED objects and the magnitudes
    # in a form that unittest can access and validate

    sedMasterList = []
    magnitudeMasterList = []

    # I need to give it the name of an actual SED file that spans the expected wavelength range
    defSedName = 'km30_5250.fits_g00_5370'
    default_columns = [('sedFilename', defSedName, (str, len(defSedName))), ('glon', 180., float),
                       ('glat', 30., float), ('galacticAv', 0.1, float), ('galacticRv', 3.1, float)]


class cartoonStarsOnlyI(InstanceCatalog, AstrometryStars, EBVmixin, VariabilityStars, PhotometryStars):
    catalog_type = 'cartoonStarsOnlyI'
    column_outputs = ['id', 'raObserved', 'decObserved', 'cartoon_i']

    # I need to give it the name of an actual SED file that spans the expected wavelength range
    defSedName = 'km30_5250.fits_g00_5370'
    default_columns = [('sedFilename', defSedName, (str, len(defSedName))), ('glon', 180., float),
                       ('glat', 30., float), ('galacticAv', 0.1, float), ('galacticRv', 3.1, float)]

    @compound('cartoon_u', 'cartoon_g', 'cartoon_r', 'cartoon_i', 'cartoon_z')
    def get_magnitudes(self):
        """
        Example photometry getter for alternative (i.e. non-LSST) bandpasses
        """
        if not hasattr(self, 'cartoonBandpassDict'):
            bandpassNames = ['u', 'g', 'r', 'i', 'z']
            bandpassDir = os.path.join(getPackageDir('sims_photUtils'), 'tests', 'cartoonSedTestData')
            self.cartoonBandpassDict = BandpassDict.loadTotalBandpassesFromFiles(bandpassNames, bandpassDir = bandpassDir,
                                                                                 bandpassRoot = 'test_bandpass_')

        return self._magnitudeGetter(self.cartoonBandpassDict, self.get_magnitudes._colnames)


class cartoonStarsIZ(cartoonStarsOnlyI):
    catalog_type = 'cartoonStarsIR'
    column_outputs = ['id', 'raObserved', 'decObserved', 'cartoon_i', 'cartoon_z']


class cartoonGalaxies(InstanceCatalog, AstrometryGalaxies, EBVmixin, VariabilityGalaxies, cartoonPhotometryGalaxies, testDefaults):
    """
    A catalog of galaxies relying on the cartoon photometry methods (which use non-LSST bandpasses
    and output extra data for use by unit tests)
    """
    catalog_type = 'cartoonGalaxies'
    column_outputs = ['galid', 'raObserved', 'decObserved',
                      'ctotal_u', 'ctotal_g', 'ctotal_r', 'ctotal_i', 'ctotal_z',
                      'cbulge_u', 'cbulge_g', 'cbulge_r', 'cbulge_i', 'cbulge_z',
                      'cdisk_u', 'cdisk_g', 'cdisk_r', 'cdisk_i', 'cdisk_z',
                      'cagn_u', 'cagn_g', 'cagn_r', 'cagn_i', 'cagn_z',
                      'sedFilenameBulge', 'magNormBulge', 'internalAvBulge',
                      'sedFilenameDisk', 'magNormDisk', 'internalAvDisk',
                      'sedFilenameAgn', 'magNormAgn', 'redshift']

    # I need to give it the name of an actual SED file that spans the expected wavelength range
    defSedName = "Inst.80E09.25Z.spec"
    default_columns = [('sedFilenameBulge', defSedName, (str, len(defSedName))),
                       ('sedFilenameDisk', defSedName, (str, len(defSedName))),
                       ('sedFilenameAgn', defSedName, (str, len(defSedName))),
                       ('glon', 210., float),
                       ('glat', 70., float),
                       ('internalAvBulge', 3.1, float),
                       ('internalAvDisk', 3.1, float)]

    default_formats = {'f': '%.12f'}

    def get_galid(self):
        return self.column_by_name('id')


class cartoonGalaxiesIG(InstanceCatalog, AstrometryGalaxies, EBVmixin, VariabilityGalaxies, cartoonPhotometryGalaxies):

    catalog_type = 'cartoonGalaxiesIG'
    column_outputs = ['galid', 'raObserved', 'decObserved', 'ctotal_i', 'ctotal_g']

    # I need to give it the name of an actual SED file that spans the expected wavelength range
    defSedName = "Inst.80E09.25Z.spec"
    default_columns = [('sedFilenameBulge', defSedName, (str, len(defSedName))),
                       ('sedFilenameDisk', defSedName, (str, len(defSedName))),
                       ('sedFilenameAgn', defSedName, (str, len(defSedName))),
                       ('glon', 210., float),
                       ('glat', 70., float),
                       ('internalAvBulge', 3.1, float),
                       ('internalAvDisk', 3.1, float)]

    default_formats = {'f': '%.12f'}

    def get_galid(self):
        return self.column_by_name('id')


class galaxiesWithHoles(InstanceCatalog, PhotometryGalaxies):
    """
    This is an InstanceCatalog of galaxies that sets some of the
    component Seds to 'None' so that we can test how sum_magnitudes
    handles NaN's in the context of a catalog.
    """
    column_outputs = ['raJ2000', 'decJ2000',
                      'lsst_u', 'lsst_g', 'lsst_r', 'lsst_i', 'lsst_z', 'lsst_y',
                      'uBulge', 'gBulge', 'rBulge', 'iBulge', 'zBulge', 'yBulge',
                      'uDisk', 'gDisk', 'rDisk', 'iDisk', 'zDisk', 'yDisk',
                      'uAgn', 'gAgn', 'rAgn', 'iAgn', 'zAgn', 'yAgn']

    default_formats = {'f': '%.12f'}

    defSedName = "Inst.80E09.25Z.spec"
    default_columns = [('glon', 210., float),
                       ('glat', 70., float),
                       ('internalAvBulge', 3.1, float),
                       ('internalAvDisk', 3.1, float)]

    def get_galid(self):
        return self.column_by_name('id')

    @compound('sedFilenameBulge', 'sedFilenameDisk', 'sedFilenameAgn')
    def get_sedNames(self):
        ra = self.column_by_name('raJ2000')
        elements = len(ra)
        bulge = []
        disk = []
        agn = []
        for ix in range(elements):
            bulge.append(self.defSedName)
            disk.append(self.defSedName)
            agn.append(self.defSedName)

        for ix in range(elements/8):
            ibase = ix*8
            if ibase+1 < elements:
                bulge[ibase+1] = 'None'
            if ibase+2 < elements:
                disk[ibase+2] = 'None'
            if ibase+3 < elements:
                agn[ibase+3] = 'None'
            if ibase+4 < elements:
                bulge[ibase+4] = 'None'
                disk[ibase+4] = 'None'
            if ibase+5 < elements:
                bulge[ibase+5] = 'None'
                agn[ibase+5] = 'None'
            if ibase+6 < elements:
                disk[ibase+6] = 'None'
                agn[ibase+6] = 'None'
            if ibase+7 < elements:
                bulge[ibase+7] = 'None'
                disk[ibase+7] = 'None'
                agn[ibase+7] = 'None'

        return numpy.array([bulge, disk, agn])


class testStars(InstanceCatalog, EBVmixin, VariabilityStars, TestVariabilityMixin, PhotometryStars, testDefaults):
    """
    A generic catalog of stars
    """
    catalog_type = 'test_stars'
    column_outputs = ['id', 'raJ2000', 'decJ2000', 'magNorm',
                      'lsst_u', 'sigma_lsst_u',
                      'lsst_g', 'sigma_lsst_g',
                      'lsst_r', 'sigma_lsst_r',
                      'lsst_i', 'sigma_lsst_i',
                      'lsst_z', 'sigma_lsst_z',
                      'lsst_y', 'sigma_lsst_y',
                      'EBV', 'varParamStr']
    defSedName = 'sed_flat.txt'
    default_columns = [('sedFilename', defSedName, (str, len(defSedName))), ('glon', 180., float),
                       ('glat', 30., float), ('galacticAv', 0.1, float), ('galacticRv', 3.1, float)]


class testGalaxies(InstanceCatalog, EBVmixin, VariabilityGalaxies, TestVariabilityMixin, PhotometryGalaxies, testDefaults):
    """
    A generic catalog of galaxies
    """
    catalog_type = 'test_galaxies'
    column_outputs = ['galid', 'raJ2000', 'decJ2000',
                      'redshift',
                      'magNormAgn', 'magNormBulge', 'magNormDisk',
                      'lsst_u', 'sigma_lsst_u',
                      'lsst_g', 'sigma_lsst_g',
                      'lsst_r', 'sigma_lsst_r',
                      'lsst_i', 'sigma_lsst_i',
                      'lsst_z', 'sigma_lsst_z',
                      'lsst_y', 'sigma_lsst_y',
                      'sedFilenameBulge', 'uBulge', 'sigma_uBulge', 'gBulge', 'sigma_gBulge',
                      'rBulge', 'sigma_rBulge', 'iBulge', 'sigma_iBulge', 'zBulge', 'sigma_zBulge',
                      'yBulge', 'sigma_yBulge',
                      'sedFilenameDisk', 'uDisk', 'sigma_uDisk', 'gDisk', 'sigma_gDisk', 'rDisk', 'sigma_rDisk',
                      'iDisk', 'sigma_iDisk', 'zDisk', 'sigma_zDisk', 'yDisk', 'sigma_yDisk',
                      'sedFilenameAgn',
                      'uAgn', 'sigma_uAgn',
                      'gAgn', 'sigma_gAgn',
                      'rAgn', 'sigma_rAgn',
                      'iAgn', 'sigma_iAgn',
                      'zAgn', 'sigma_zAgn',
                      'yAgn', 'sigma_yAgn', 'varParamStr']
    defSedName = "sed_flat.txt"
    default_columns = [('sedFilename', defSedName, (str, len(defSedName))),
                       ('sedFilenameAgn', defSedName, (str, len(defSedName))),
                       ('sedFilenameBulge', defSedName, (str, len(defSedName))),
                       ('sedFilenameDisk', defSedName, (str, len(defSedName))),
                       ('glon', 210., float),
                       ('glat', 70., float),
                       ]

    def get_internalAvDisk(self):
        return numpy.ones(len(self._current_chunk))*0.1

    def get_internalAvBulge(self):
        return numpy.ones(len(self._current_chunk))*0.1

    def get_galid(self):
        return self.column_by_name('id')
