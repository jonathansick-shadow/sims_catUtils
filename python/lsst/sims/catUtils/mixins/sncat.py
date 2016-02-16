"""
Mixin to InstanceCatalog class to give SN catalogs in catsim
"""
import numpy as np

from lsst.sims.catalogs.measures.instance import InstanceCatalog
from lsst.sims.catalogs.measures.instance import compound
from lsst.sims.photUtils import BandpassDict
from lsst.sims.photUtils import Bandpass
from lsst.sims.catUtils.mixins import CosmologyMixin
from lsst.sims.catUtils.mixins import PhotometryBase
import lsst.sims.photUtils.PhotometricParameters as PhotometricParameters

import astropy

from lsst.sims.catUtils.supernovae import SNObject
from lsst.sims.catUtils.supernovae import SNUniverse


__all__ = ['SNIaCatalog', 'SNFunctionality', 'FrozenSNCat']
cosmo = CosmologyMixin()

class SNFunctionality(object):
    """
    SNFunctionality is a mixin that provides functionality of getting fluxes
    and magnitudes for SN defined by parameters of `~sims_catUtils.SNObject` as
    defined in `~sims_catUtils/python/lsst/sims/catUtils/supernovae/SNObject`


    This class is not meant to be used by itself, as it does not have any way
    of obtaining its attributes, but as a mixin to classes like SNIaCatalog
    which define these attributes.
    """

    # Write the location of SED file (for example for PhoSim)
    writeSedFile = False
    # prefix to use for SED File name
    prefix = ''

    # t0, c, x_1, x_0 are parameters characterizing a SALT
    # based SN model as defined in sncosmo
    column_outputs = ['snid', 'snra', 'sndec', 'z', 't0', 'c', 'x1', 'x0']

    suppressHighzSN = True
    maxTimeSNVisible = 100.
    maxz = 1.2
    # Flux variables are convenient to display in exponential format to avoid
    # having them cut off
    variables = ['flux_u', 'flux_g', 'flux_r', 'flux_i', 'flux_z', 'flux_y']
    variables += ['flux', 'flux_err', 'mag_err']

    override_formats = {'snra': '%8e', 'sndec': '%8e', 'c': '%8e',
                        'x0': '%8e'}
    for var in variables:
        override_formats[var] = '%8e'
    # You can add parameters like fluxes and magnitudes by adding the following
    # variables to the list
    # 'flux_u', 'flux_g', 'flux_r', 'flux_i', 'flux_z', 'flux_y' ,
    # 'mag_u', 'mag_g', 'mag_r', 'mag_i', 'mag_z', 'mag_y']
    cannot_be_null = ['x0', 'z', 't0']

    @astropy.utils.lazyproperty
    def mjdobs(self):
        '''
        The time of observation for the catalog, which is set to be equal
        to obs_metadata.mjd
        '''
        return self.obs_metadata.mjd.TAI

    @astropy.utils.lazyproperty
    def badvalues(self):
        '''
        The representation of bad values in this catalog is numpy.nan
        '''
        return np.nan

    @property
    def suppressDimSN(self):
        """
        Boolean to decide whether to output observations of SN that are too dim
        should be represented in the catalog or not. By default set to True
        """
        if not hasattr(self, '_suppressDimSN'):
            suppressDimSN_default = True
            self._suppressDimSN = suppressDimSN_default
        return self._suppressDimSN

    @suppressDimSN.setter
    def suppressDimSN(self, suppressDimSN):
        """
        set the value of suppressDimSN of the catalog Parameters
        Parameters
        ----------
        supressDimSN : Boolean, mandatory
            Value to set suppressDimSN to
        """
        self._suppressDimSN = suppressDimSN
        return self._suppressDimSN 

    @astropy.utils.lazyproperty
    def photometricparameters(self, expTime=15., nexp=2):
        lsstPhotometricParameters = PhotometricParameters(exptime=expTime,
                                                          nexp=nexp)
        return lsstPhotometricParameters

    @astropy.utils.lazyproperty
    def lsstBandpassDict(self):
        return BandpassDict.loadTotalBandpassesFromFiles()

    @astropy.utils.lazyproperty
    def observedIndices(self):
        bandPassNames = self.obs_metadata.bandpass
        return [self.lsstBandpassDict.keys().index(x) for x in bandPassNames]

    @compound('TsedFilepath', 'TmagNorm')
    def get_phosimVars(self):
        """
        Obtain variables TsedFilepath to be used to obtain unique filenames
        for each SED for phoSim and TMagNorm which is also used.
        """
        # construct the unique filename
        # method: snid_mjd(to 4 places of decimal)_bandpassname
        mjd = "_{:0.4f}_".format(self.mjdobs)
        mjd += self.obs_metadata.bandpass + '.dat'
        fnames = np.array([self.prefix + 'specFile_' + str(int(elem)) + mjd
                  for elem in self.column_by_name('snid')], dtype='str')

        c, x1, x0, t0  = self.column_by_name('c'),\
                         self.column_by_name('x1'),\
                         self.column_by_name('x0'),\
                         self.column_by_name('t0')

        bp = Bandpass()
        bp.imsimBandpass()

        magNorms = np.zeros(len(fnames))

        snobject = SNObject()
        for i in range(len(self.column_by_name('snid'))):
            if np.isnan(t0[i]):
                magNorms[i] = np.nan
                fnames[i] = None

            else:
                snobject.set(c=c[i], x1=x1[i], x0=x0[i], t0=t0[i])

                # SED in rest frame
                sed = snobject.SNObjectSourceSED(time=self.mjdobs)
                try:
                    magNorms[i] = sed.calcMag(bandpass=bp)
                except:
                    # sed.flambda = 1.0e-20 
                    magNorms[i] = 1000. # sed.calcMag(bandpass=bp)

                if self.writeSedFile:
                    print('writing file to ', fnames[i])
                    sed.writeSED(fnames[i])


        return (fnames, magNorms)


    def load_SNsed(self):
        """
        returns a list of SN seds in `lsst.sims.photUtils.Sed` observed within
        the spatio-temporal range specified by obs_metadata

        """
        c, x1, x0, t0, _z, ra, dec = self.column_by_name('c'),\
            self.column_by_name('x1'),\
            self.column_by_name('x0'),\
            self.column_by_name('t0'),\
            self.column_by_name('redshift'),\
            self.column_by_name('raJ2000'),\
            self.column_by_name('decJ2000')

        SNobject = SNObject()

        sedlist = []
        for i in range(self.numobjs):
            SNobject.set(z=_z[i], c=c[i], x1=x1[i], t0=t0[i], x0=x0[i])
            SNobject.setCoords(ra=ra[i], dec=dec[i])
            SNobject.mwEBVfromMaps()
            sed = SNobject.SNObjectSED(time=self.mjdobs,
                                       bandpass=self.lsstBandpassDict,
                                       applyExitinction=True)
            sedlist.append(sed)

        return sedlist

    @property
    def numobjs(self):
        return len(self.column_by_name('snid'))

    def get_time(self):

        return np.repeat(self.mjdobs, self.numobjs)

    def get_band(self):
        bandname = self.obs_metadata.bandpass
        return np.repeat(bandname, self.numobjs)

    @compound('flux', 'mag', 'flux_err', 'mag_err', 'adu')
    def get_snbrightness(self):

        c, x1, x0, t0, _z, ra, dec = self.column_by_name('c'),\
            self.column_by_name('x1'),\
            self.column_by_name('x0'),\
            self.column_by_name('t0'),\
            self.column_by_name('redshift'),\
            self.column_by_name('raJ2000'),\
            self.column_by_name('decJ2000')

        SNobject = SNObject()
        bandname = self.obs_metadata.bandpass
        if isinstance(bandname, list):
            raise ValueError('bandname expected to be string, but is list\n')
        bandpass = self.lsstBandpassDict[bandname]

        _photParams = PhotometricParameters()
        # Initialize return array
        vals = np.zeros(shape=(self.numobjs, 5))

        for i, _ in enumerate(vals):
            SNobject.set(z=_z[i], c=c[i], x1=x1[i], t0=t0[i], x0=x0[i])
            SNobject.setCoords(ra=ra[i], dec=dec[i])
            SNobject.mwEBVfromMaps()

            # Calculate fluxes
            fluxinMaggies = SNobject.catsimBandFlux(time=self.mjdobs,
                                                    bandpassobject=bandpass)
            mag = SNobject.catsimBandMag(time=self.mjdobs,
                                         fluxinMaggies=fluxinMaggies,
                                         bandpassobject=bandpass)
            vals[i, 0] = fluxinMaggies
            vals[i, 1] = mag
            flux_err = SNobject.catsimBandFluxError(time=self.mjdobs,
                                                    bandpassobject=bandpass,
                                                    m5=self.obs_metadata.m5[
                                                        bandname],
                                                    photParams=None,
                                                    fluxinMaggies=fluxinMaggies,
                                                    magnitude=mag)
            sed = SNobject.SNObjectSED(time=self.mjdobs,
                                       bandpass=self.lsstBandpassDict,
                                                                                                  applyExtinction=True)
            adu = sed.calcADU(bandpass, photParams=_photParams)
            mag_err = SNobject.catsimBandMagError(time=self.mjdobs,
                                                  bandpassobject=bandpass,
                                                  m5=self.obs_metadata.m5[
                                                      bandname],
                                                  photParams=_photParams,
                                                  magnitude=mag)
            vals[i, 2] = flux_err
            vals[i, 3] = mag_err
            vals[i, 4] = adu
        return (vals[:, 0], vals[:, 1], vals[:, 2], vals[:, 3], vals[:, 4])

    @compound('flux_u', 'flux_g', 'flux_r', 'flux_i', 'flux_z', 'flux_y',
              'mag_u', 'mag_g', 'mag_r', 'mag_i', 'mag_z', 'mag_y',
              'adu_u', 'adu_g', 'adu_r', 'adu_i', 'adu_z', 'adu_y', 'mwebv')
    def get_snfluxes(self):

        c, x1, x0, t0, _z, ra, dec = self.column_by_name('c'),\
            self.column_by_name('x1'),\
            self.column_by_name('x0'),\
            self.column_by_name('t0'),\
            self.column_by_name('redshift'),\
            self.column_by_name('raJ2000'),\
            self.column_by_name('decJ2000')

        SNobject = SNObject()
        # Initialize return array
        vals = np.zeros(shape=(self.numobjs, 19))
        for i, _ in enumerate(vals):
            SNobject.set(z=_z[i], c=c[i], x1=x1[i], t0=t0[i], x0=x0[i])
            SNobject.setCoords(ra=ra[i], dec=dec[i])
            SNobject.mwEBVfromMaps()
            # Calculate fluxes
            vals[i, :6] = SNobject.catsimManyBandFluxes(time=self.mjdobs,
                                                        bandpassDict=self.lsstBandpassDict,
                                                        observedBandPassInd=None)
            # Calculate magnitudes
            vals[i, 6:12] = SNobject.catsimManyBandMags(time=self.mjdobs,
                                                        bandpassDict=self.lsstBandpassDict,
                                                        observedBandPassInd=None)

            vals[i, 12:18] = SNobject.catsimManyBandADUs(time=self.mjdobs,
                                                bandpassDict=self.lsstBandpassDict,
                                                photParams=self.photometricparameters)
            vals[i, 18] = SNobject.ebvofMW
        return (vals[:, 0], vals[:, 1], vals[:, 2], vals[:, 3],
                vals[:, 4], vals[:, 5], vals[:, 6], vals[:, 7],
                vals[:, 8], vals[:, 9], vals[:, 10], vals[:, 11],
                vals[:, 12], vals[:, 13], vals[:, 14], vals[:, 15],
                vals[:, 16], vals[:, 17], vals[:, 18])



class SNIaCatalog (SNFunctionality,  InstanceCatalog, CosmologyMixin, SNUniverse):

    """
    `lsst.sims.catalogs.measures.instance.InstanceCatalog` class with SN
    characterized by the  following attributes

    Attributes
    ----------
    column_outputs :
    suppressHighzSN :
    maxTimeSNVisible :
    maxz :
    variables :
    override_formats :
    cannot_be_null :
    mjdobs :
    badvalues position :
    3-tuple of floats (ra, dec, redshift), velocity : 3 tuple of floats
        velocity wrt host galaxy in Km/s, the supernova model (eg. SALT2)
    and parameters of the supernova model that predict the SED.
    """

##    # t_0, c, x_1, x_0 are parameters characterizing a SALT
##    # based SN model as defined in sncosmo
##    column_outputs = ['snid', 'snra', 'sndec', 'z', 't0', 'c', 'x1', 'x0']
##
##    suppressHighzSN = True
##    maxTimeSNVisible = 100.
##    maxz = 1.2
##    # Flux variables are convenient to display in exponential format to avoid
##    # having them cut off
##    variables = ['flux_u', 'flux_g', 'flux_r', 'flux_i', 'flux_z', 'flux_y']
##    variables += ['flux', 'flux_err', 'mag_err']
##
##    override_formats = {'snra': '%8e', 'sndec': '%8e', 'c': '%8e',
##                        'x0': '%8e'}
##    for var in variables:
##        override_formats[var] = '%8e'
##    # You can add parameters like fluxes and magnitudes by adding the following
##    # variables to the list
##    # 'flux_u', 'flux_g', 'flux_r', 'flux_i', 'flux_z', 'flux_y' ,
##    # 'mag_u', 'mag_g', 'mag_r', 'mag_i', 'mag_z', 'mag_y']
##    cannot_be_null = ['x0', 'z', 't0']
##
##    @astropy.utils.lazyproperty
##    def mjdobs(self):
##        '''
##        The time of observation for the catalog, which is set to be equal
##        to obs_metadata.mjd
##        '''
##        return self.obs_metadata.mjd.TAI
##
##    @astropy.utils.lazyproperty
##    def badvalues(self):
##        '''
##        The representation of bad values in this catalog is numpy.nan
##        '''
##        return np.nan
##
##    @property
##    def suppressDimSN(self):
##        """
##        Boolean to decide whether to output observations of SN that are too dim
##        should be represented in the catalog or not. By default set to True
##        """
##        if not hasattr(self, '_suppressDimSN'):
##            suppressDimSN_default = True
##            self._suppressDimSN = suppressDimSN_default
##        return self._suppressDimSN
##
##    @suppressDimSN.setter
##    def suppressDimSN(self, suppressDimSN):
##        """
##        set the value of suppressDimSN of the catalog Parameters
##        Parameters
##        ----------
##        supressDimSN : Boolean, mandatory
##            Value to set suppressDimSN to
##        """
##        self._suppressDimSN = suppressDimSN
##        return self._suppressDimSN 
##
##    @astropy.utils.lazyproperty
##    def photometricparameters(self, expTime=15., nexp=2):
##        lsstPhotometricParameters = PhotometricParameters(exptime=expTime,
##                                                          nexp=nexp)
##        return lsstPhotometricParameters
##
##    @astropy.utils.lazyproperty
##    def lsstBandpassDict(self):
##        return BandpassDict.loadTotalBandpassesFromFiles()
##
##    @astropy.utils.lazyproperty
##    def observedIndices(self):
##        bandPassNames = self.obs_metadata.bandpass
##        return [self.lsstBandpassDict.keys().index(x) for x in bandPassNames]
##
    def get_snid(self):
        # Not necessarily unique if the same galaxy hosts two SN
        # Use refIdCol to access the relevant id column of the dbobj
        # Should revert to galTileID for galaxyTiled catalogDBObj and
        # id for galaxyObj catalogDBObj
        # (email from Scott)
       return self.column_by_name(self.refIdCol)


    @compound('snra', 'sndec', 'z', 'vra', 'vdec', 'vr')
    def get_angularCoordinates(self):
        '''
        Obtain the coordinates and velocity of the SN from the host galaxy

        Returns
        -------
        `np.ndarray` of coordinara, dec, z, vra, vdec, and vr

        '''
        hostra, hostdec, hostz = self.column_by_name('raJ2000'),\
            self.column_by_name('decJ2000'),\
            self.column_by_name('redshift')
        snra, sndec, snz, snvra, snvdec, snvr = self.SNCoordinatesFromHost(
            hostra, hostdec, hostz)

        return ([snra, sndec, snz, snvra, snvdec, snvr])

    @compound('c', 'x1', 'x0', 't0')
    def get_snparams(self):
        hostz, hostid, hostmu = self.column_by_name('redshift'),\
            self.column_by_name('snid'),\
            self.column_by_name('cosmologicalDistanceModulus')

        vals = self.SNparamDistFromHost(hostz, hostid, hostmu)

        return (vals[:, 0], vals[:, 1], vals[:, 2], vals[:, 3])




class FrozenSNCat(SNFunctionality,  InstanceCatalog, CosmologyMixin, SNUniverse):

    """
    `lsst.sims.catalogs.measures.instance.InstanceCatalog` class with SN
    characterized by the  following attributes

    Attributes
    ----------
    column_outputs :
    suppressHighzSN :
    maxTimeSNVisible :
    maxz :
    variables :
    override_formats :
    cannot_be_null :
    mjdobs :
    badvalues position :
    3-tuple of floats (ra, dec, redshift), velocity : 3 tuple of floats
        velocity wrt host galaxy in Km/s, the supernova model (eg. SALT2)
    and parameters of the supernova model that predict the SED.
    """

    surveyStartDate = 59580. # For Kraken_1042

    #def get_snid(self):

    #    return self.column_by_name('Tsnid')


    @compound('snra', 'sndec', 'z', 'vra', 'vdec', 'vr')
    def get_angularCoordinates(self):
        '''
        Obtain the coordinates and velocity of the SN from the host galaxy

        Returns
        -------
        `np.ndarray` of coordinara, dec, z, vra, vdec, and vr

        '''
        snra, sndec, snz = self.column_by_name('raJ2000'),\
            self.column_by_name('decJ2000'),\
            self.column_by_name('Tredshift')
        snvra = np.zeros(self.numobjs)
        snvdec = np.zeros(self.numobjs)
        snvr = np.zeros(self.numobjs)

        return (snra, sndec, snz, snvra, snvdec, snvr)

    @compound('c', 'x1', 'x0', 't0')
    def get_snparams(self):

        c, x1, x0 = self.column_by_name('Tc'), \
                    self.column_by_name('Tx1'),\
                    self.column_by_name('Tx0')
        t0 = self.column_by_name('Tt0') + self.surveyStartDate
        if self.suppressDimSN :
            print('badvalues ', self.badvalues)
            print('mjd ', self.mjdobs)
            print('maxTime', self.maxTimeSNVisible)
            print('number of cases ',
                    len(t0[np.abs(t0 - self.mjdobs) > self.maxTimeSNVisible]))
            t0 = np.where(np.abs(t0 - self.mjdobs) > self.maxTimeSNVisible,
                      self.badvalues, t0)

        return (c, x1, x0, t0)

