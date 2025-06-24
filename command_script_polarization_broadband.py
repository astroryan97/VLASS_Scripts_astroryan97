# -*- coding: utf-8 -*-
'''
Created on Wed Jun 11 15:30:36 2025

@author: Ryan Johnston (Univeristy of Alberta)

Based on code from Erik Carlson (https://github.com/erikvcarlson/VLASS_Scripts)

This script 
'''
import os
from inspect import signature
from pipeline.utils import readParameterFile
from casatasks import tclean

__rethrow_casa_exceptions = True #standard
context = h_init() #standard
context.set_state('ProjectSummary', 'proposal_code', 'VLASS') #standard
context.set_state('ProjectSummary', 'proposal_title', 'unknown') #standard
context.set_state('ProjectSummary', 'piname', 'unknown') #standard
context.set_state('ProjectSummary', 'observatory', 'Karl G. Jansky Very Large Array') #standard
context.set_state('ProjectSummary', 'telescope', 'EVLA') #standard
context.set_state('ProjectStructure', 'ppr_file', 'PPR.xml') #standard
context.set_state('ProjectStructure', 'recipe_name', 'hifv_vlassSEIP') #standard


# Change the vis variable to the location of your measurement set
vis = ['J0925+1444_VLASS_split.ms']

# Change the vlass_ql_database_path to your VLASS1Q.fits file path
vlass_ql_database_path = '/home/vlass/packages/VLASS1Q.fits'

# Change the parameter_file to your image parameter file
param_list='SEIP_parameter.list'

parm_list = readParameterFile('SEIP_parameter.list')

# extract vis and session for import 
vis_list = parm_list[0].get('vis', [])

if not isinstance(vis_list, list):
    vis_list = [vis_list]
#session_list = [f"session_{i+1}" for i in range(len(vis_list))]

valid_tclean_args = set(signature(tclean).parameters)

tclean_kwargs = {k: v for k, v in parm_list.items() if k in valid_tclean_args}
tclean_kwargs['vis'] = vis_list

#for p in parm_list:
#    if p.get('stokes') == 'V':
#        # Keep only keys that tclean actually accepts
#        tclean_kwargs = {k: v for k, v in p.items() if k in valid_tclean_args}
#        # Ensure vis is sourced from the parameter file
#        tclean_kwargs['vis'] = vis_list

try:
    hifv_importdata(nocopy=True, vis=vis_list, session=['session_1'])
    #change the vis variable to the location of your measurement set
    hif_editimlist(parameter_file='SEIP_parameter.list')
    #change the parameter_file to your image parameter file
    hif_transformimagedata(datacolumn='data', clear_pointing=False, modify_weights=True, wtmode='nyq')
    hifv_vlassmasking(maskingmode='vlass-se-tier-1', vlass_ql_database='/home/rsjohns1/VLASS12Q_CIRADA.fits')
    hif_makeimages(hm_masking='manual')
    hifv_checkflag(checkflagmode='vlass-imaging')
    hifv_statwt(statwtmode='VLASS-SE', datacolumn='residual_data')
    hifv_selfcal(selfcalmode='VLASS-SE')

    tclean(**tclean_kwargs)

    
    #tclean(
    #    vis=['HD_321958_2_2_split.ms'],
    #    imagename='HD_321958_StokesV3_Broadband',
    #    phasecenter='J2000 16:46:40.294 -38.08.50.739',
    #    datacolumn='corrected',
    #    specmode='mfs',           
    #    deconvolver='clarkstokes',
    #    nterms=1,                 
    #    stokes='V',               
    #    gridder='mosaic',
    #    imsize=[4096,4096],
    #    cell='0.6arcsec',
    #    weighting='briggs', #briggs
    #    robust=0.5,
    #    niter=1000,              
    #    threshold='0.0mJy',      
    #    usemask='auto-multithresh', #'auto-multithresh'
    #    interactive=False,
    #    pbcor=True # True False
    #)

    tclean(
        vis = vis,
        imagename = 'field_IQUV_awp',
        datacolumn = 'corrected',
        field = '',
        specmode = 'mfs',
        spw = '',
        deconvolver = 'mtmfs',
        nterms = 2,             # spectral behaviour for I & Q/U
        gridder = 'awproject',  # use A-Projection
        aterm = True,          # apply antenna A-term (PB) per pol
        wbawp = True,          # wide-band AW-project (MT-MFS + PB)
        conjbeams = True,      # enforce conjugate symmetry of beams
        stokes = 'V',
        imsize = [2048,2048],
        cell = '0.6arcsec',
        weighting = 'briggs',
        robust  = 0.5,
        niter = 10000,
        threshold = '0.03mJy',
        usemask = 'auto-multithresh',
        interactive = False
    )

    tclean(
        vis = vis,
        imagename = 'field_V_awp',
        datacolumn = 'corrected',
        field = '',
        spw = '',
        specmode = 'mfs',            # continuum synthesis
        deconvolver = 'mtmfs',
        nterms = 1,                # only the average term for V
        gridder = 'awproject',      # apply the polarization-dependent PB
        aterm = True,
        wbawp = True,             # wide-band A-Projection
        conjbeams = True,
        stokes = 'V',              # ← only circular pol
        imsize = [2048, 2048],
        cell = '0.6arcsec',
        weighting = 'briggs',
        robust = 0.5,
        niter = 20000,            # go deeper for faint V
        threshold = '0.01mJy',        # push down to ~3×σ_V
        usemask = 'auto-multithresh',
        interactive = False,
        pbcor = True              # CASA 6+ can do PB-corr in tclean
    )


    # I-plane
    imsubimage(
        imagename='field_IQUV.image',
        outfile='field_I.image',
        stokes='I')
    # Q-plane
    imsubimage(
        imagename='field_IQUV.image',
        outfile='field_Q.image',
        stokes='Q')
    # U-plane
    imsubimage(
        imagename='field_IQUV.image',
        outfile='field_U.image',
        stokes='U')
    # V-plane
    imsubimage(
        imagename='field_IQUV.image',
        outfile='field_V.image',
        stokes='V')

    # define your output folder (relative to your CASA working dir, or absolute)
    #outdir = 'VLASS_StokesV'
    os.makedirs(outdir, exist_ok = True)

    # after your tclean/impbcor steps, export into that folder
    exportfits(
        imagename = imagename + '.pbcor',                 # e.g. 'JXXXX+XXXX_StokesV.pbcor'
        fitsimage = os.path.join(outdir, imagename + '_pbcor.fits'),
        overwrite = True
    )

    
    # Export the image to FITS
    exportfits(
        imagename = 'HD_321958_StokesV3_Broadband.image',
        fitsimage = 'HD_321958_StokesV3_Broadband.fits',
        overwrite = True,
        dropstokes = False,
        dropdeg = True
    )

finally:
    h_save()
