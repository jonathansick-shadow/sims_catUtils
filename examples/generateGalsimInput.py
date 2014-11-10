"""
This file shows how to generate a GalSim input catalog named galSim_example.txt

"""

from __future__ import with_statement
from lsst.sims.catalogs.measures.instance import InstanceCatalog
from lsst.sims.catalogs.generation.db import CatalogDBObject, ObservationMetaData
from lsst.sims.catUtils.exampleCatalogDefinitions.galSimCatalogExamples import \
        GalSimGalaxies

from lsst.sims.catUtils.baseCatalogModels import *

from lsst.obs.lsstSim import LsstSimMapper
import numpy

#starObjNames = ['msstars', 'bhbstars', 'wdstars', 'rrlystars', 'cepheidstars']

obsMD = CatalogDBObject.from_objid('opsim3_61')
obs_metadata = obsMD.getObservationMetaData(88625744, 0.01, makeCircBounds = True)



gals = CatalogDBObject.from_objid('galaxyBulge')

#now append a bunch of objects with 2D sersic profiles to our output file
galaxy_galSim = GalSimGalaxies(gals, obs_metadata=obs_metadata)
mapper = LsstSimMapper()
galaxy_galSim.camera = mapper.camera
galaxy_galSim.write_catalog('galSim_example.txt')
print obs_metadata.bounds.radius
