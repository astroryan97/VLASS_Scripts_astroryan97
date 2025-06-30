# -*- coding: utf-8 -*-
'''
Created on Wed Jun 11 15:30:36 2025

@author: Ryan Johnston (Univeristy of Alberta)

Based on code from Erik Carlson (https://github.com/erikvcarlson/VLASS_Scripts)
See  VLASS Memo #20 for more info.

This script runs the VLASS Single‐Epoch Imaging Pipeline (SEIP) to create total intensity (Stokes I) VLASS images.

Makes use of the the VLASS QL component catalog to create initial CLEAN masks.
The catalog (VLASS1Q.fits) contains PyBDSF-fitted sources from Epoch 1 QL images and is used to automatically create CLEAN masks around detected radio sources.
Download from: http://www.aoc.nrao.edu/~akimball/VLASS/VLASS1Q.fits if using locally
(Updated version with Epochs 1 & 2: VLASS12Q_CIRADA.fits)
'''
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
param_list = 'SEIP_parameter.list'


try:
    # Import the raw visibility data into pipeline
    hifv_importdata(nocopy = True, vis = vis, session = ['session_1'])

    ''' First imaging step '''
    # Add to a list of images to be produced with hif_makeimages()
    # uses hif_tclean() to invoke CASA tclean
    # Many of the hif_editimlist() inputs map directly to tclean parameters
    hif_editimlist(parameter_file = param_list)

    # Extract fields for the desired VLASS image to a new MS and reset weights if desired
    hif_transformimagedata(datacolumn = 'data', clear_pointing = False, modify_weights = True, wtmode = 'nyq')

    # Generate initial CLEAN masks using the VLASS QL component catalog
    hifv_vlassmasking(maskingmode = 'vlass-se-tier-1', vlass_ql_database = vlass_ql_database_path)

    # Compute clean map - Compute clean results from a list of specified targets
    hif_makeimages(hm_masking = 'manual')
    
    # Check and flag bad data based on VLASS‐imaging standards
    # Flag possible RFI using rflag and tfcrop
    hifv_checkflag(checkflagmode = 'vlass-imaging')

    # Calculate data weights based on stdev within each spw
    # Recompute statistical weights on the residual data
    hifv_statwt(statwtmode = 'VLASS-SE', datacolumn = 'residual_data')

    # Perform phase-only self-calibration, per scan row, on VLASS SE images
    # Selfcal task executing gaincal and applycal
    hifv_selfcal(selfcalmode = 'VLASS-SE')
    
    ''' Second imaging cycle (after self-cal) '''
    # Reload the imaging parameter list cause why not
    hif_editimlist(parameter_file=param_list)

    # Re‐image with manual masks after selfcalibration
    #change the parameter_file to your image parameter file
    hif_makeimages(hm_masking = 'manual')

    ''' Final imaging step '''
    # Reload parameters again before the Tier-2 masking step
    hif_editimlist(parameter_file=param_list)

    # Generate a more aggressive Tier-2 CLEAN mask
    # change the parameter_file to your image parameter file
    hifv_vlassmasking(maskingmode = 'vlass-se-tier-2')

    # Final imaging pass using the Tier-2 mask
    hif_makeimages(hm_masking = 'manual')

    # Apply primary beam correction to final VLA/VLASS images
    hifv_pbcor(pipelinemode = "automatic")

    # Creates RMS (noise) maps for each image
    # Primary beam corrected tt0 images
    hif_makermsimages(pipelinemode = "automatic")

    # Make cutout images centered on source
    hif_makecutoutimages(pipelinemode = "automatic")

    # Compute in‐band spectral indices (alpha)
    # Extract spectral index from intensity peak in VLA/VLASS images
    hif_analyzealpha(pipelinemode = "automatic")

    # Export all pipeline products to products directory converting and or packing it as necessary
    hifv_exportvlassdata(pipelinemode = "automatic") 
    
finally:
    # Save pipeline’s internal state and any unsaved products
    h_save()