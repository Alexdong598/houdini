import os
import hou
import toolutils

def lookDev_Kit():
    startframe = 1001
    turntableTime = 100
    lightspinTime = 100
    envmap = hou.ui.selectFile(start_directory = "U:\_HDRI\Above the Cloud")

    #define TT subject
    model = hou.selectedNodes()[0]
    name = model.name()
    model_pos = model.position()


    #############TTrig#################
    background = hou.node("/stage")
    TTrigNode = background.createNode("sopcreate", "TTrig")
    TTrigNodePos = TTrigNode.position()

    TTrigNodesopContext = background.node(TTrigNode.name() + "/sopnet/create")
    TTrig_import = TTrigNodesopContext.createNode("alembic", "TTrig_import")
    TTrig_import.parm("fileName").set("X:/pipelinernd_rnd-0192/_temp/Bo/houdini_lookDev_kit/lookDev_rig_v002.abc")
    TTrig_import_pos = TTrig_import.position()

    TTrig_grp = TTrigNodesopContext.createNode("alembicgroup", "TTrig_grp")
    TTrig_grp.parm("group0").set("refBalls")
    TTrig_grp.parm("objectPath0").set("/lookDev_rig_grp/references_grp")
    TTrig_grp.setPosition(TTrig_import_pos + hou.Vector2(0, -1))
    TTrig_grp.setInput(0, TTrig_import)
    TTrig_grp_pos = TTrig_grp.position()

    blast = TTrigNodesopContext.createNode("blast", "onlyTTrig")
    blast.parm("group").set("refBalls")
    blast.parm("grouptype").set(4)
    blast.parm("negate").set(1)
    blast.setPosition(TTrig_grp_pos + hou.Vector2(0, -1))
    blast.setInput(0, TTrig_grp)
    blast_pos = blast.position()

    matchsize = TTrigNodesopContext.createNode("matchsize", "backToOrigin")
    matchsize.parm("justify_y").set(1)
    matchsize.setPosition(blast_pos + hou.Vector2(0, -1))
    matchsize.setInput(0, blast)
    matchsize_pos = matchsize.position()

    output = TTrigNodesopContext.createNode("output", "OUTPUT")
    output.setPosition(matchsize_pos + hou.Vector2(0, -1))
    output.setInput(0, matchsize)
    output.setDisplayFlag(True)
    output.setRenderFlag(True)

    ####################TTrig_trans##############
    TTrig_trans = background.createNode("xform", "TTrig_trans")
    TTrig_trans.setPosition(TTrigNodePos + hou.Vector2(0, -1))
    TTrig_trans.setInput(0, TTrigNode)
    TTrig_trans_pos = TTrig_trans.position()

    myttrigpos = (0.43, -0.27, -1.385)
    TTrig_trans.parmTuple("t").set(myttrigpos)
    TTrig_trans.parm("scale").set(0.07)

    #############TTrig_mtl#################
    TTrig_mtl = background.createNode("materiallibrary", "TTrig_mtl")
    TTrig_mtl.setPosition(TTrig_trans_pos + hou.Vector2(0, -1))
    TTrig_mtl.setInput(0, TTrigNode)
    TTrig_mtl_pos = TTrig_mtl.position()

    chromeBall1_mtl = TTrig_mtl.createNode("arnold_materialbuilder", "chromeBall1_mtl")
    chromeBall2_mtl = TTrig_mtl.createNode("arnold_materialbuilder", "chromeBall2_mtl")
    chromeBall3_mtl = TTrig_mtl.createNode("arnold_materialbuilder", "chromeBall3_mtl")
    checkMac_mtl = TTrig_mtl.createNode("arnold_materialbuilder", "checkMac_mtl")
    TTrig_mtl.layoutChildren()

    checkMac_OUT_material = checkMac_mtl.node("OUT_material")
    checkMac_shd = checkMac_mtl.createNode("arnold::standard_surface", "checkMac_shd")
    checkMac_OUT_material.setInput(0, checkMac_shd)
    checkMac_diff = checkMac_mtl.createNode("image", "checkMac_diff")
    checkMac_shd.setInput(1, checkMac_diff)
    checkMac_mtl.layoutChildren()

    #################chromeBall1#######################
    chromeBall1_OUT_material = chromeBall1_mtl.node("OUT_material")
    chromeBall1_shd = chromeBall1_mtl.createNode("arnold::standard_surface", "chromeBall1_shd")
    chromeBall1_shd.parm("base").set(0.3)
    chromeBall1_shd.parm("metalness").set(1.0)
    chromeBall1_shd.parm("specular_roughness").set(0.1)
    chromeBall1_OUT_material.setInput(0, chromeBall1_shd)
    chromeBall1_mtl.layoutChildren()

    #################chromeBall2#######################
    chromeBall2_OUT_material = chromeBall2_mtl.node("OUT_material")
    chromeBall2_shd = chromeBall2_mtl.createNode("arnold::standard_surface", "chromeBall2_shd")
    chromeBall2_shd.parmTuple("base_color").set((0.2, 0.2, 0.2))
    chromeBall2_shd.parm("metalness").set(0.0)
    chromeBall2_shd.parm("specular_roughness").set(0.2)
    chromeBall2_shd.parm("specular_IOR").set(1.5)
    chromeBall2_OUT_material.setInput(0, chromeBall2_shd)
    chromeBall2_mtl.layoutChildren()

    #################chromeBall3#######################
    chromeBall3_OUT_material = chromeBall3_mtl.node("OUT_material")
    chromeBall3_shd = chromeBall3_mtl.createNode("arnold::standard_surface", "chromeBall3_shd")
    chromeBall3_shd.parmTuple("base_color").set((0.8, 0.8, 0.8))
    chromeBall3_shd.parm("metalness").set(0.0)
    chromeBall3_shd.parm("specular_roughness").set(0.2)
    chromeBall3_shd.parm("specular_IOR").set(1.5)
    chromeBall3_OUT_material.setInput(0, chromeBall3_shd)
    chromeBall3_mtl.layoutChildren()

    checkMac_diff.parm("filename").set("U:/_textures/ColorChecker/ColorChecker2014/ACEScg_ColorChecker2014.exr")

    TTrig_mtl.parm("materials").set(0)
    TTrig_mtl.parm("materials").set(4)

    TTrig_mtl.parm("matnode1").set("chromeBall1_mtl")
    TTrig_mtl.parm("matpath1").set("chromeBall1_mtl")
    TTrig_mtl.parm("geopath1").set("/lookDev_rig_grp/references_grp/chrome_ball_geo/chrome_ball_geoShape")

    TTrig_mtl.parm("matnode2").set("chromeBall2_mtl")
    TTrig_mtl.parm("matpath2").set("chromeBall2_mtl")
    TTrig_mtl.parm("geopath2").set("/lookDev_rig_grp/references_grp/grey_ball_geo/grey_ball_geoShape")

    TTrig_mtl.parm("matnode3").set("chromeBall3_mtl")
    TTrig_mtl.parm("matpath3").set("chromeBall3_mtl")
    TTrig_mtl.parm("geopath3").set("/lookDev_rig_grp/references_grp/white_ball_geo/white_ball_geoShape")

    TTrig_mtl.parm("matnode4").set("checkMac_mtl")
    TTrig_mtl.parm("matpath4").set("checkMac_mtl")
    TTrig_mtl.parm("geopath4").set("/lookDev_rig_grp/references_grp/macbeth_geo/macbeth_geoShape")

    TTrig_subnet = background.collapseIntoSubnet((TTrigNode, TTrig_trans, TTrig_mtl), "Turntable_subnet")
    TTrig_mtlNew = TTrig_subnet.node("TTrig_mtl")
    TTrig_mtlNew_pos = TTrig_mtlNew.position()
    TTrig_output = TTrig_subnet.createNode("output", "output")
    TTrig_output.setPosition(TTrig_mtlNew_pos + hou.Vector2(0, -1))
    TTrig_output.setInput(0, TTrig_mtlNew)
    TTrig_output.setDisplayFlag(True)


    #######################################################################################################
    ##############create stair############################
    stair = background.createNode("sopcreate", "stair")

    stair.setPosition(model_pos + hou.Vector2(1.5, 1))

    # Access the SOP network inside the sopcreate node
    sop_network = background.node(stair.path()+"/sopnet/create")

    # Initial position for the first node
    current_position = hou.Vector2(0, 0)

    # Create the objmerge node
    objmerge = sop_network.createNode("object_merge", "assetInput")
    objmerge.setPosition(current_position)
    # Customize objmerge node parameters here if needed
    objmerge.parm("objpath1").set(model.path() + "/sopnet/OUT")

    # Move position down for the next node
    current_position += hou.Vector2(0, -2)

    # Create the tube node
    tube = sop_network.createNode("tube", "tube1")
    tube.setPosition(current_position)
    tube.setInput(0, objmerge)  # Connect to objmerge
    # Customize tube node parameters here if needed
    tube.parm("type").set(1)
    tube.parm("cap").set(1)
    tube.parm("cols").set(60)

    #set up bounding box 
    min_vecBbox = tube.geometry().boundingBox().minvec()
    max_vecBbox = tube.geometry().boundingBox().maxvec()
    bbox_sizeX = (max_vecBbox - min_vecBbox)[1]*1.5
    bbox_sizeY = (max_vecBbox - min_vecBbox)[1]

    # Move position down for the next node
    current_position += hou.Vector2(0, -2)

    # Create the matchsize node
    matchsizeStair = sop_network.createNode("matchsize", "matchsizeStair")
    matchsizeStair.setPosition(current_position)
    matchsizeStair.setInput(0, tube)  # Connect to tube
    # Customize matchsize parameters here if needed
    matchsizeStair.parm("justify_y").set(1)

    # Move position down for the next node
    current_position += hou.Vector2(0, -2)

    # Create the transform node
    transformStair = sop_network.createNode("xform", "transformStair")
    transformStair.setPosition(current_position)
    transformStair.setInput(0, matchsizeStair)  # Connect to matchsize
    # Customize transform parameters here if needed
    transformStair.parm("scale").set(2.0)

    # Move position down for the next node
    current_position += hou.Vector2(0, -2)

    # Create the blast node
    blastStair = sop_network.createNode("blast", "blastStair")
    blastStair.setPosition(current_position)
    blastStair.setInput(0, transformStair)  # Connect to transform
    # Customize blast parameters here if needed
    blastStair.parm("group").set("1")
    blastStair.parm("grouptype").set(4)
    blastStair.parm("negate").set(1)

    # Move position down for the next node
    current_position += hou.Vector2(0, -2)
    # Create the polyextrude node
    polyextrude = sop_network.createNode("polyextrude::2.0", "polyextrude1")
    polyextrude.setPosition(current_position)
    polyextrude.setInput(0, blastStair)  # Connect to blast
    # Customize polyextrude parameters here if needed
    polyextrude.parm("dist").set(bbox_sizeX)

    polyextrude.parm("outputback").set(1)
    # Move position down for the next node
    current_position += hou.Vector2(0, -2)

    # Create the final output node
    output = sop_network.createNode("output", "OUT")
    output.setPosition(current_position)
    output.setInput(0, polyextrude)  # Connect to polyextrude

    # Set the display and render flags on the output node
    output.setDisplayFlag(True)
    output.setRenderFlag(True)

    ######################################################################################
    ###############create human template#################
    human = background.createNode("sopcreate", "human")
    human.setPosition(model_pos + hou.Vector2(-1.5, 0))
    humanSubFolder = background.node(human.path()+"/sopnet/create")

    paul = humanSubFolder.createNode("labs::testgeometry_paul::2.0", "Paul")
    paul_pos = paul.position()

    paul_matchSize = humanSubFolder.createNode("matchsize", "paul_matchSize")
    paul_matchSize.parm("justify_y").set(1)
    paul_matchSize.setPosition(paul_pos + hou.Vector2(0, -1))
    paul_matchSize.setInput(0, paul)
    paul_matchSizePos = paul_matchSize.position()

    paul_transform = humanSubFolder.createNode("xform", "paul_transform")
    paul_transform.parm("tx").set(-bbox_sizeY)
    paul_transform.setPosition(paul_matchSizePos + hou.Vector2(0, -1))
    paul_transform.setInput(0, paul_matchSize)
    paul_transformPos = paul_transform.position()


    human_OUT = humanSubFolder.createNode("output", "OUT")
    human_OUT.setPosition(paul_transformPos + hou.Vector2(0, -1))
    human_OUT.setInput(0, paul_transform)

    ##########set up human material##################
    human.parm("materials").set(1) 

    human.parm("matnode1").set("sopnet/create/Paul/quickmaterial1/matnet/Material_1") 
    human.parm("matpath1").set('`ifs(ch("enable_pathprefix"), chs("pathprefix"), "")`/materials/Material_1')
    human.parm("geopath1").set('`ifs(ch("enable_pathprefix"), chs("pathprefix")+"/geo1/shop_materialpath_"+strreplace(opfullpath("."), "/", "_")+"_sopnet_create_Paul_quickmaterial1_matnet_Material_1", "/Geometry/geo1/shop_materialpath_"+strreplace(opfullpath("."), "/", "_")+"_sopnet_create_Paul_quickmaterial1_matnet_Material_1")`') 

    #####################################################################################################
    #align model and TTrig
    mdlTTrigDist = 4
    TTrig_subnet.setPosition(model_pos + hou.Vector2(mdlTTrigDist,0))
    TTrig_subnet_pos = TTrig_subnet.position()

    mergeMdlTTrig = background.createNode("merge", "mergeMdlTTrig")
    mergeMdlTTrig.setPosition(model_pos + hou.Vector2(mdlTTrigDist*0.5,-2))
    mergeMdlTTrig_pos = mergeMdlTTrig.position()
    mergeMdlTTrig.setInput(0,human)
    mergeMdlTTrig.setInput(1,model)
    mergeMdlTTrig.setInput(2,stair)
    mergeMdlTTrig.setInput(3,TTrig_subnet)


    # Create transform node
    transform = background.createNode("xform","globalTrans")
    transform.setPosition(TTrig_subnet_pos+hou.Vector2(3,2))
    TTrig_subnet.setInput(0,transform)
    transform_pos = transform.position()

    # Create null node
    null = background.createNode("primitive","null")
    null.setPosition(transform_pos+hou.Vector2(0,2))
    transform.setInput(0,null)
    null_pos = null.position()


    # Create OBJ camera first
    objClass = background.node("/obj")
    camName = "Turntable_cam_"+name
    for node in objClass.children():
        if node.type().name() == "cam" and node.name().startswith(camName):
            node.destroy()
    cam = objClass.createNode("cam",camName)
    # cam.parm("focal").set(50)
    # cam.parm("aperture").set(41.4214)

    # Get model's center position and bounds
    mdlGeo = background.node(model.path()+"/sopnet/create")
    for child in mdlGeo.children():
        if child.isDisplayFlagSet():
            displayNode = child

    bbox = displayNode.geometry().boundingBox()
    model_center = bbox.center()
    bbox_size = bbox.sizevec()

    # Set camera position
    cam_distance = 5
    cam_z_offset = bbox_size[2] * 0.5 + cam_distance
    cam.parmTuple("t").set((model_center[0], model_center[1], model_center[2] + cam_z_offset))

    # Create LOP camera
    lopCam = background.createNode("sceneimport::2.0",camName)
    lopCam.parm("objdestpath").set("`lopinputprim('.', 0)`")
    lopCam.parm("objects").set(cam.path())
    lopCam.setPosition(transform_pos+hou.Vector2(0,-2))
    lopCam.setInput(0,transform)
    lopCam_pos = lopCam.position()

    # Frame camera on model
    viewer = toolutils.sceneViewer().curViewport()
    viewer.lockCameraToView(True)
    model.setSelected(1,1)
    viewer.frameSelected()
    viewer.saveViewToCamera(cam)
    viewer.setCamera(cam)

    # Now update TTrig position relative to camera view
    TTrig_trans = TTrig_subnet.node("TTrig_trans")
    if TTrig_trans:
        cam_pos = cam.evalParmTuple("t")
        # Position TTrig in front and bottom-left of camera view
        ttrig_pos = (
            cam_pos[0] - bbox_size[0] * 0.3,  # Left of camera
            cam_pos[1] - bbox_size[1] * 0.3,  # Below camera
            cam_pos[2] - bbox_size[2] * 0.5   # In front of camera
        )
        TTrig_trans.parmTuple("t").set(ttrig_pos)
        TTrig_trans.parm("scale").set(0.07)

    #create light
    domeLight = background.createNode("domelight::2.0", "TTrig_dome")
    domeLight.parm("xn__inputstexturefile_r3ah").set(envmap)
    domeLight.setPosition(lopCam_pos + hou.Vector2(3,0))


    #create sublayer
    sublayer = background.createNode("sublayer","sublayer")
    sublayer.setPosition(lopCam_pos+hou.Vector2(0,-4))
    sublayer.setInput(0,mergeMdlTTrig)
    sublayer.setInput(1,lopCam)
    sublayer.setInput(2,domeLight)
    sublayer_pos = sublayer.position()

    ############################################################################
    #TTrig transform
    TTrig_nodeNew = TTrig_subnet.node("TTrig")
    TTrig_nodeNew.parm("tx").set(1.83)
    TTrig_nodeNew.parm("ty").set(-0.35)
    TTrig_nodeNew.parm("tz").set(transform.parm("tz").eval())

    TTrig_nodeNew.parm("tz").setExpression("transform.parm(\"tz\").eval()", hou.exprLanguage.Python)



    ######### DEFINE KEYFRAMES ########
    #startframe turntableTime lightspinTime
    startTT = startframe
    endTT = startframe + turntableTime
    startSpin = endTT + 1
    endSpin = startSpin + lightspinTime

    #set houdini playbar
    hou.playbar.setFrameRange(startTT, endSpin)
    hou.playbar.setPlaybackRange(startTT, endSpin)

    #defining a dictionary containing the keyframes and their values
    dictTT={startTT : 0, endTT : 360}
    dictSpin={startSpin: 0, endSpin : 360}

    for data in dictTT:
        key = hou.Keyframe()
        key.setFrame(data)
        key.setValue(dictTT.get(data))
        model.parm("ry").setKeyframe(key)

    for data in dictSpin:
        key = hou.Keyframe()
        key.setFrame(data)
        key.setValue(dictSpin.get(data))
        domeLight.parm("ry").setKeyframe(key) 

    #add arnold render setting
    arnoldRenderSetting = background.createNode("arnold_rendersettings","arnoldRenderSetting")
    arnoldRenderSetting.setPosition(sublayer_pos + hou.Vector2(0,-2))
    arnoldRenderSetting.setInput(0,sublayer)
    arnoldRenderSetting.parm("camera").set("/" + null.name() + "/" + camName)
    arnoldRenderSetting.parm("resolution1").set(1920)
    arnoldRenderSetting.parm("resolution2").set(1080)
    arnoldRenderSetting.parm("xn__arnoldglobalAA_samples_wcbg").set(3)
    arnoldRenderSetting.parm("xn__arnoldglobalGI_diffuse_samples_xpbg").set(3)
    arnoldRenderSetting.parm("xn__arnoldglobalGI_specular_samples_krbg").set(3)
    arnoldRenderSetting.parm("xn__arnoldglobalGI_transmission_samples_2xbg").set(3)
    arnoldRenderSetting.parm("xn__arnoldglobalGI_sss_samples_fjbg").set(3)
    arnoldRenderSetting.parm("xn__arnoldglobalGI_volume_samples_bobg").set(0)

    arnoldRenderSetting_pos = arnoldRenderSetting.position()
    arnoldRenderSetting.setDisplayFlag(True)

    #add userender_rop
    userender_rop = background.createNode("usdrender_rop","usdrender_rop")
    userender_rop.parm("trange").set(1)
    userender_rop.parm("f1").deleteAllKeyframes()
    userender_rop.parm("f2").deleteAllKeyframes()
    userender_rop.parm("f1").setExpression("startTT", hou.exprLanguage.Python)
    userender_rop.parm("f2").setExpression("endSpin", hou.exprLanguage.Python)
    userender_rop.setPosition(arnoldRenderSetting_pos + hou.Vector2(0,-2))
    userender_rop.setInput(0,arnoldRenderSetting)



