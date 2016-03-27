import os
import numpy as np
import unittest
import lsst.utils.tests as utilsTests

from lsst.utils import getPackageDir
from lsst.sims.utils import ObservationMetaData
from lsst.sims.catalogs.generation.db import fileDBObject
from lsst.sims.catalogs.measures.instance import InstanceCatalog
from lsst.sims.catUtils.mixins import PhotometryStars, PhotometrySSM, \
    PhotometryGalaxies


class baselineStarCatalog(InstanceCatalog, PhotometryStars):
    column_outputs = ['raJ2000', 'decJ2000',
                      'lsst_u', 'lsst_g', 'lsst_r', 'lsst_i', 'lsst_z', 'lsst_y',
                      'sigma_lsst_u', 'sigma_lsst_g', 'sigma_lsst_r',
                      'sigma_lsst_i', 'sigma_lsst_z', 'sigma_lsst_y']

    default_formats = {'f': '%.13f'}


class uStarCatalog(InstanceCatalog, PhotometryStars):
    column_outputs = ['raJ2000', 'decJ2000', 'lsst_u', 'sigma_lsst_u']

    default_formats = {'f': '%.13f'}


class gzStarCatalog(InstanceCatalog, PhotometryStars):
    column_outputs = ['raJ2000', 'decJ2000', 'lsst_g', 'lsst_z',
                      'sigma_lsst_g', 'sigma_lsst_z']

    default_formats = {'f': '%.13f'}


class gzUncertaintyStarCatalog(InstanceCatalog, PhotometryStars):
    column_outputs = ['raJ2000', 'decJ2000', 'sigma_lsst_g', 'sigma_lsst_z']

    default_formats = {'f': '%.13f'}


class IndexTestCaseStars(unittest.TestCase):
    """
    This unit test suite will test that the 'indices' framework for making
    sure that an InstanceCatalog only calculates the magnitudes requested
    works in the case of stars.
    """

    @classmethod
    def setUpClass(cls):

        cls.obs = ObservationMetaData(bandpassName=['u', 'g', 'r', 'i', 'z', 'y'],
                                      m5 = [22.0, 23.0, 24.0, 25.0, 26.0, 27.0])

        baselineDtype = np.dtype([(name, np.float) for name in baselineStarCatalog.column_outputs])

        dbdtype = np.dtype([
                           ('id', np.int),
                           ('raJ2000', np.float),
                           ('decJ2000', np.float),
                           ('sedFilename', str, 100),
                           ('magNorm', np.float),
                           ('galacticAv', np.float)
                           ])

        inputDir = os.path.join(getPackageDir('sims_catUtils'), 'tests', 'testData')
        inputFile = os.path.join(inputDir, 'IndicesTestCatalogStars.txt')

        cls.db = fileDBObject(inputFile, runtable='test',
                              idColKey='id', dtype=dbdtype)

        cat = baselineStarCatalog(cls.db, obs_metadata=cls.obs)
        cls.catName = os.path.join(getPackageDir('sims_catUtils'), 'tests',
                                   'scratchSpace', 'indicesStarsControlCat.txt')

        cat.write_catalog(cls.catName)
        cls.controlData = np.genfromtxt(cls.catName, dtype=baselineDtype, delimiter=',')

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.catName):
            os.unlink(cls.catName)

    def test_u_star_catalog(self):
        """
        Test that a catalog which only cares about u does not calculate any other magnitudes.
        """
        catName = os.path.join(getPackageDir('sims_catUtils'), 'tests', 'scratchSpace', 'indicesUCat.txt')
        dtype = np.dtype([(name, np.float) for name in uStarCatalog.column_outputs])

        cat = uStarCatalog(self.db, obs_metadata=self.obs)
        cat.write_catalog(catName)
        testData = np.genfromtxt(catName, dtype=dtype, delimiter=',')
        np.testing.assert_array_almost_equal(self.controlData['raJ2000'], testData['raJ2000'], 10)
        np.testing.assert_array_almost_equal(self.controlData['decJ2000'], testData['decJ2000'], 10)
        np.testing.assert_array_almost_equal(self.controlData['lsst_u'], testData['lsst_u'], 10)
        np.testing.assert_array_almost_equal(self.controlData['sigma_lsst_u'], testData['sigma_lsst_u'], 10)

        self.assertTrue('lsst_g' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_g' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_z' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_z' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_y' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_y' not in cat._actually_calculated_columns)

        if os.path.exists(catName):
            os.unlink(catName)

    def test_gz_star_catalog(self):
        """
        Test that a catalog which only cares about g and z does not calculate any other magnitudes
        """
        catName = os.path.join(getPackageDir('sims_catUtils'), 'tests', 'scratchSpace', 'indicesGZCat.txt')
        dtype = np.dtype([(name, np.float) for name in gzStarCatalog.column_outputs])

        cat = gzStarCatalog(self.db, obs_metadata=self.obs)
        cat.write_catalog(catName)
        testData = np.genfromtxt(catName, dtype=dtype, delimiter=',')
        np.testing.assert_array_almost_equal(self.controlData['raJ2000'], testData['raJ2000'], 10)
        np.testing.assert_array_almost_equal(self.controlData['decJ2000'], testData['decJ2000'], 10)
        np.testing.assert_array_almost_equal(self.controlData['lsst_g'], testData['lsst_g'], 10)
        np.testing.assert_array_almost_equal(self.controlData['sigma_lsst_g'], testData['sigma_lsst_g'], 10)
        np.testing.assert_array_almost_equal(self.controlData['lsst_z'], testData['lsst_z'], 10)
        np.testing.assert_array_almost_equal(self.controlData['sigma_lsst_z'], testData['sigma_lsst_z'], 10)

        self.assertTrue('lsst_u' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_u' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_y' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_y' not in cat._actually_calculated_columns)

        if os.path.exists(catName):
            os.unlink(catName)

    def test_gz_uncertainty_star_catalog(self):
        """
        Test that a catalog which only cares about g and z uncertainties does not calculate any other magnitudes
        """
        catName = os.path.join(getPackageDir('sims_catUtils'), 'tests',
                               'scratchSpace', 'indicesGZUncertaintyCat.txt')
        dtype = np.dtype([(name, np.float) for name in gzUncertaintyStarCatalog.column_outputs])

        cat = gzUncertaintyStarCatalog(self.db, obs_metadata=self.obs)
        cat.write_catalog(catName)
        testData = np.genfromtxt(catName, dtype=dtype, delimiter=',')
        np.testing.assert_array_almost_equal(self.controlData['raJ2000'], testData['raJ2000'], 10)
        np.testing.assert_array_almost_equal(self.controlData['decJ2000'], testData['decJ2000'], 10)
        np.testing.assert_array_almost_equal(self.controlData['sigma_lsst_g'], testData['sigma_lsst_g'], 10)
        np.testing.assert_array_almost_equal(self.controlData['sigma_lsst_z'], testData['sigma_lsst_z'], 10)

        self.assertTrue('lsst_u' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_u' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_y' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_y' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_g' in cat._actually_calculated_columns)
        self.assertTrue('lsst_z' in cat._actually_calculated_columns)

        if os.path.exists(catName):
            os.unlink(catName)


class baselineSSMCatalog(InstanceCatalog, PhotometrySSM):
    column_outputs = ['lsst_u', 'lsst_g', 'lsst_r', 'lsst_i', 'lsst_z', 'lsst_y',
                      'sigma_lsst_u', 'sigma_lsst_g', 'sigma_lsst_r',
                      'sigma_lsst_i', 'sigma_lsst_z', 'sigma_lsst_y']

    default_formats = {'f': '%.13f'}


class uSSMCatalog(InstanceCatalog, PhotometrySSM):
    column_outputs = ['lsst_u', 'sigma_lsst_u']

    default_formats = {'f': '%.13f'}


class gzSSMCatalog(InstanceCatalog, PhotometrySSM):
    column_outputs = ['lsst_g', 'lsst_z',
                      'sigma_lsst_g', 'sigma_lsst_z']

    default_formats = {'f': '%.13f'}


class gzUncertaintySSMCatalog(InstanceCatalog, PhotometrySSM):
    column_outputs = ['sigma_lsst_g', 'sigma_lsst_z']

    default_formats = {'f': '%.13f'}


class IndexTestCaseSSM(unittest.TestCase):
    """
    This unit test suite will test that the 'indices' framework for making
    sure that an InstanceCatalog only calculates the magnitudes requested
    works in the case of solar system objects.
    """

    @classmethod
    def setUpClass(cls):

        cls.obs = ObservationMetaData(bandpassName=['u', 'g', 'r', 'i', 'z', 'y'],
                                      m5 = [22.0, 23.0, 24.0, 25.0, 26.0, 27.0])

        baselineDtype = np.dtype([(name, np.float) for name in baselineSSMCatalog.column_outputs])

        dbdtype = np.dtype([
                           ('id', np.int),
                           ('sedFilename', str, 100),
                           ('magNorm', np.float),
                           ('velRA', np.float),
                           ('velDec', np.float)
                           ])

        inputDir = os.path.join(getPackageDir('sims_catUtils'), 'tests', 'testData')
        inputFile = os.path.join(inputDir, 'SSMphotometryCatalog.txt')

        cls.db = fileDBObject(inputFile, runtable='test',
                              idColKey='id', dtype=dbdtype)

        cat = baselineSSMCatalog(cls.db, obs_metadata=cls.obs)
        cls.catName = os.path.join(getPackageDir('sims_catUtils'), 'tests',
                                   'scratchSpace', 'indicesSSMControlCat.txt')

        cat.write_catalog(cls.catName)
        cls.controlData = np.genfromtxt(cls.catName, dtype=baselineDtype, delimiter=',')

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.catName):
            os.unlink(cls.catName)

    def test_u_ssm_catalog(self):
        """
        Test that a catalog which only cares about u does not calculate any other magnitudes.
        """
        catName = os.path.join(getPackageDir('sims_catUtils'), 'tests', 'scratchSpace', 'indicesUssmCat.txt')
        dtype = np.dtype([(name, np.float) for name in uSSMCatalog.column_outputs])

        cat = uSSMCatalog(self.db, obs_metadata=self.obs)
        cat.write_catalog(catName)
        testData = np.genfromtxt(catName, dtype=dtype, delimiter=',')
        np.testing.assert_array_almost_equal(self.controlData['lsst_u'], testData['lsst_u'], 10)
        np.testing.assert_array_almost_equal(self.controlData['sigma_lsst_u'], testData['sigma_lsst_u'], 10)

        self.assertTrue('lsst_g' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_g' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_z' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_z' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_y' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_y' not in cat._actually_calculated_columns)

        if os.path.exists(catName):
            os.unlink(catName)

    def test_gz_ssm_catalog(self):
        """
        Test that a catalog which only cares about g and z does not calculate any other magnitudes
        """
        catName = os.path.join(getPackageDir('sims_catUtils'), 'tests', 'scratchSpace', 'indicesGZssmCat.txt')
        dtype = np.dtype([(name, np.float) for name in gzSSMCatalog.column_outputs])

        cat = gzSSMCatalog(self.db, obs_metadata=self.obs)
        cat.write_catalog(catName)
        testData = np.genfromtxt(catName, dtype=dtype, delimiter=',')
        np.testing.assert_array_almost_equal(self.controlData['lsst_g'], testData['lsst_g'], 10)
        np.testing.assert_array_almost_equal(self.controlData['sigma_lsst_g'], testData['sigma_lsst_g'], 10)
        np.testing.assert_array_almost_equal(self.controlData['lsst_z'], testData['lsst_z'], 10)
        np.testing.assert_array_almost_equal(self.controlData['sigma_lsst_z'], testData['sigma_lsst_z'], 10)

        self.assertTrue('lsst_u' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_u' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_y' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_y' not in cat._actually_calculated_columns)

        if os.path.exists(catName):
            os.unlink(catName)

    def test_gz_uncertainty_ssm_catalog(self):
        """
        Test that a catalog which only cares about g and z uncertainties does not calculate any other magnitudes
        """
        catName = os.path.join(getPackageDir('sims_catUtils'), 'tests',
                               'scratchSpace', 'indicesGZssmUncertaintyCat.txt')
        dtype = np.dtype([(name, np.float) for name in gzUncertaintySSMCatalog.column_outputs])

        cat = gzUncertaintySSMCatalog(self.db, obs_metadata=self.obs)
        cat.write_catalog(catName)
        testData = np.genfromtxt(catName, dtype=dtype, delimiter=',')
        np.testing.assert_array_almost_equal(self.controlData['sigma_lsst_g'], testData['sigma_lsst_g'], 10)
        np.testing.assert_array_almost_equal(self.controlData['sigma_lsst_z'], testData['sigma_lsst_z'], 10)

        self.assertTrue('lsst_u' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_u' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_y' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_y' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_g' in cat._actually_calculated_columns)
        self.assertTrue('lsst_z' in cat._actually_calculated_columns)

        if os.path.exists(catName):
            os.unlink(catName)


class baselineGalaxyCatalog(InstanceCatalog, PhotometryGalaxies):
    column_outputs = ['uBulge', 'gBulge', 'rBulge', 'iBulge', 'zBulge', 'yBulge',
                      'uDisk', 'gDisk', 'rDisk', 'iDisk', 'zDisk', 'yDisk',
                      'uAgn', 'gAgn', 'rAgn', 'iAgn', 'zAgn', 'yAgn',
                      'lsst_u', 'lsst_g', 'lsst_r', 'lsst_i', 'lsst_z', 'lsst_y',
                      'sigma_uBulge', 'sigma_gBulge', 'sigma_rBulge',
                      'sigma_iBulge', 'sigma_zBulge', 'sigma_yBulge',
                      'sigma_uDisk', 'sigma_gDisk', 'sigma_rDisk',
                      'sigma_iDisk', 'sigma_zDisk', 'sigma_yDisk',
                      'sigma_uAgn', 'sigma_gAgn', 'sigma_rAgn',
                      'sigma_iAgn', 'sigma_zAgn', 'sigma_yAgn',
                      'sigma_lsst_u', 'sigma_lsst_g', 'sigma_lsst_r',
                      'sigma_lsst_i', 'sigma_lsst_z', 'sigma_lsst_y']

    default_formats = {'f': '%.13f'}


class uGalaxyCatalog(InstanceCatalog, PhotometryGalaxies):
    column_outputs = ['uBulge', 'uDisk', 'uAgn', 'lsst_u',
                      'sigma_uBulge', 'sigma_uDisk', 'sigma_uAgn',
                      'sigma_lsst_u']

    default_formats = {'f': '%.13f'}


class gzGalaxyCatalog(InstanceCatalog, PhotometryGalaxies):
    column_outputs = ['gBulge', 'gDisk', 'gAgn', 'lsst_g',
                      'zBulge', 'zDisk', 'zAgn', 'lsst_z',
                      'sigma_gBulge', 'sigma_gDisk', 'sigma_gAgn',
                      'sigma_lsst_g',
                      'sigma_zBulge', 'sigma_zDisk', 'sigma_zAgn',
                      'sigma_lsst_z']

    default_formats = {'f': '%.13f'}


class IndexTestCaseGalaxies(unittest.TestCase):
    """
    This unit test suite will test that the 'indices' framework for making
    sure that an InstanceCatalog only calculates the magnitudes requested
    works in the case of galaxies.
    """

    @classmethod
    def setUpClass(cls):

        cls.obs = ObservationMetaData(bandpassName=['u', 'g', 'r', 'i', 'z', 'y'],
                                      m5=[24.0, 25.0, 26.0, 27.0, 28.0, 29.0])

        dtype = np.dtype([
                         ('id', np.int),
                         ('sedFilenameBulge', str, 100),
                         ('magNormBulge', np.float),
                         ('sedFilenameDisk', str, 100),
                         ('magNormDisk', np.float),
                         ('sedFilenameAgn', str, 100),
                         ('magNormAgn', np.float),
                         ('internalAvBulge', np.float),
                         ('internalAvDisk', np.float),
                         ('galacticAv', np.float),
                         ('redshift', np.float)
                         ])

        inputDir = os.path.join(getPackageDir('sims_catUtils'), 'tests', 'testData')
        inputFile = os.path.join(inputDir, 'IndicesTestCatalogGalaxies.txt')
        cls.db = fileDBObject(inputFile, dtype=dtype, runtable='test',
                              idColKey='id')

        cls.db.objectTypeId = 44

        catName = os.path.join(getPackageDir('sims_catUtils'), 'tests',
                               'scratchSpace', 'galaxyPhotIndicesBaseline.txt')

        cat = baselineGalaxyCatalog(cls.db, obs_metadata=cls.obs)
        cat.write_catalog(catName)

        dtype = np.dtype([(name, np.float) for name in cat.column_outputs])

        cls.controlData = np.genfromtxt(catName, dtype=dtype, delimiter=',')

        if os.path.exists(catName):
            os.unlink(catName)

    def test_u_catalog(self):
        """
        Test that a catalog which only requests u band magnitudes does not
        calculate anything it shouldn't
        """
        catName = os.path.join(getPackageDir('sims_catUtils'), 'tests',
                               'scratchSpace', 'galPhotIndicesUTestCat.txt')
        cat = uGalaxyCatalog(self.db, obs_metadata=self.obs)
        dtype = np.dtype([(name, np.float) for name in cat.column_outputs])
        cat.write_catalog(catName)

        testData = np.genfromtxt(catName, dtype=dtype, delimiter=',')

        for name in ('uBulge', 'uDisk', 'uAgn', 'lsst_u',
                     'sigma_uBulge', 'sigma_uDisk', 'sigma_uAgn', 'sigma_lsst_u'):

            np.testing.assert_array_almost_equal(testData[name],
                                                 self.controlData[name], 10)

        self.assertTrue('gBulge' not in cat._actually_calculated_columns)
        self.assertTrue('rBulge' not in cat._actually_calculated_columns)
        self.assertTrue('iBulge' not in cat._actually_calculated_columns)
        self.assertTrue('zBulge' not in cat._actually_calculated_columns)
        self.assertTrue('yBulge' not in cat._actually_calculated_columns)
        self.assertTrue('gDisk' not in cat._actually_calculated_columns)
        self.assertTrue('rDisk' not in cat._actually_calculated_columns)
        self.assertTrue('iDisk' not in cat._actually_calculated_columns)
        self.assertTrue('zDisk' not in cat._actually_calculated_columns)
        self.assertTrue('yDisk' not in cat._actually_calculated_columns)
        self.assertTrue('gAgn' not in cat._actually_calculated_columns)
        self.assertTrue('rAgn' not in cat._actually_calculated_columns)
        self.assertTrue('iAgn' not in cat._actually_calculated_columns)
        self.assertTrue('zAgn' not in cat._actually_calculated_columns)
        self.assertTrue('yAgn' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_g' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_z' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_y' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_gBulge' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_rBulge' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_iBulge' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_zBulge' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_yBulge' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_gDisk' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_rDisk' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_iDisk' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_zDisk' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_yDisk' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_gAgn' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_rAgn' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_iAgn' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_zAgn' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_yAgn' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_g' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_z' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_y' not in cat._actually_calculated_columns)

        if os.path.exists(catName):
            os.unlink(catName)

    def test_gz_catalog(self):
        """
        Test that a catalog which only requests g and z band magnitudes does not
        calculate anything it shouldn't
        """
        catName = os.path.join(getPackageDir('sims_catUtils'), 'tests',
                               'scratchSpace', 'galPhotIndicesGZTestCat.txt')
        cat = gzGalaxyCatalog(self.db, obs_metadata=self.obs)
        dtype = np.dtype([(name, np.float) for name in cat.column_outputs])
        cat.write_catalog(catName)

        testData = np.genfromtxt(catName, dtype=dtype, delimiter=',')

        for name in ('gBulge', 'gDisk', 'gAgn', 'lsst_g',
                     'zBulge', 'zDisk', 'zAgn', 'lsst_z',
                     'sigma_gBulge', 'sigma_gDisk', 'sigma_gAgn',
                     'sigma_lsst_g',
                     'sigma_zBulge', 'sigma_zDisk', 'sigma_zAgn',
                     'sigma_lsst_z'):

            np.testing.assert_array_almost_equal(testData[name],
                                                 self.controlData[name], 10)

        self.assertTrue('uBulge' not in cat._actually_calculated_columns)
        self.assertTrue('rBulge' not in cat._actually_calculated_columns)
        self.assertTrue('iBulge' not in cat._actually_calculated_columns)
        self.assertTrue('yBulge' not in cat._actually_calculated_columns)
        self.assertTrue('uDisk' not in cat._actually_calculated_columns)
        self.assertTrue('rDisk' not in cat._actually_calculated_columns)
        self.assertTrue('iDisk' not in cat._actually_calculated_columns)
        self.assertTrue('yDisk' not in cat._actually_calculated_columns)
        self.assertTrue('uAgn' not in cat._actually_calculated_columns)
        self.assertTrue('rAgn' not in cat._actually_calculated_columns)
        self.assertTrue('iAgn' not in cat._actually_calculated_columns)
        self.assertTrue('yAgn' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_u' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('lsst_y' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_uBulge' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_rBulge' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_iBulge' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_yBulge' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_uDisk' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_rDisk' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_iDisk' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_yDisk' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_uAgn' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_rAgn' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_iAgn' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_yAgn' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_u' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_r' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_i' not in cat._actually_calculated_columns)
        self.assertTrue('sigma_lsst_y' not in cat._actually_calculated_columns)

        if os.path.exists(catName):
            os.unlink(catName)


def suite():
    utilsTests.init()
    suites = []
    suites += unittest.makeSuite(IndexTestCaseStars)
    suites += unittest.makeSuite(IndexTestCaseSSM)
    suites += unittest.makeSuite(IndexTestCaseGalaxies)
    return unittest.TestSuite(suites)


def run(shouldExit = False):
    utilsTests.run(suite(), shouldExit)

if __name__ == "__main__":
    run(True)
