# Utinni SWG Client Address Catalog

Hardcoded SWG client memory addresses used by Utinni to hook into the Star Wars Galaxies client. Scope: `UtinniCore/`, `UtINI/`, `Launcher/`, `UtinniCoreDotNet/`. External libraries (`external/`) excluded.

**Total: 272 addresses**

## Categories

- **fn** — function entry point (called via typedef'd function pointer)
- **data** — static data pointer (usually in `0x019xxxxx`–`0x01Axxxxx`, SWG's `.data`)
- **patch** — instruction address Utinni writes bytes to (inline detour / NOP)
- **ret** — return target after a 5-byte JMP trampoline

---

## Client / Game core

### `UtinniCore/swg/client/client.cpp`
- `0x00401050` — :41 — fn — `Client::clientMain` (PE entrypoint)
- `0x00A9F970` — :40 — fn — `Client::setupStartDataInstall`
- `0x00AA0970` — :43 — fn — SWG's `WndProc`
- `0x00A9F640` — :45 — fn — `Client::writeCrashLog`
- `0x00A8A170` — :46 — fn — `Client::writeMiniDump`
- `0x00A9F766` — :172 — patch — `start_MidCrashLogWrite` (jmp patch site)
- `0x00A9F76B` — :173 — ret — `return_MidCrashLogWrite`
- `0x0193C268` — :178 — data — crash-log filename input pointer

### `UtinniCore/swg/game/game.cpp`
- `0x00422E80` — :54 — fn — `Game::install`
- `0x00423720` — :55 — fn — `Game::quit`
- `0x004237C0` — :56 — fn — `Game::mainLoop`
- `0x00424220` — :58 — fn — `Game::setupScene`
- `0x00423700` — :59 — fn — `Game::cleanupScene`
- `0x00425140` — :61 — fn — `Game::getPlayer`
- `0x004251D0` — :62 — fn — `Game::getPlayerCreatureObject`
- `0x00425BB0` — :64 — fn — `Game::getCamera`
- `0x00425BE0` — :65 — fn — `Game::getConstCamera`
- `0x00425C10` — :67 — fn — `Game::isViewFirstPerson`
- `0x00426170` — :68 — fn — `Game::isHudSceneTypeSpace`
- `0x01908830` — :108 — data — main loop counter
- `0x01908858` — :307 — data — game state flag 1 (`isSafeToUse`)
- `0x01919410` — :307 — data — game state flag 2 (`isSafeToUse`)

---

## Camera

### `UtinniCore/swg/camera/camera.cpp`
- `0x00767DF0` — :43 — fn — `Camera::getViewportInt`
- `0x00767E40` — :44 — fn — `Camera::getViewportFloat`
- `0x00767E90` — :46 — fn — `Camera::setViewport`
- `0x00767EC0` — :48 — fn — `Camera::setNearPlane`
- `0x00767EE0` — :49 — fn — `Camera::setFarPlane`
- `0x00767F00` — :51 — fn — `Camera::setHorizontalFieldOfView`
- `0x007682B0` — :53 — fn — `Camera::reverseProjectInViewportSpaceInt`
- `0x00768390` — :54 — fn — `Camera::reverseProjectInViewportSpaceFloat`
- `0x00778FE0` — :62 — fn — `Camera::addExcludedObject`
- `0x00779130` — :63 — fn — `Camera::clearExcludedObjects`
- `0x00788740` — :70 — fn — `Camera::alter`

### `UtinniCore/swg/camera/debug_camera.cpp`
- `0x006DA1B0` — :35 — fn — `DebugCamera::alter`
- `0x0051AA8D` — :309 — patch — debug camera hook site

---

## Graphics

### `UtinniCore/swg/graphics/graphics.cpp`
- `0x007548A0` — :57 — fn — `Graphics::install`
- `0x00755700` — :59 — fn — `Graphics::update`
- `0x00755730` — :60 — fn — `Graphics::beginScene`
- `0x00755740` — :61 — fn — `Graphics::endScene`
- `0x00755810` — :63 — fn — `Graphics::presentWindow`
- `0x00755800` — :64 — fn — `Graphics::present`
- `0x00755940` — :66 — fn — `Graphics::useHardwareCursor`
- `0x00755A50` — :67 — fn — `Graphics::showMouseCursor`
- `0x00755AC0` — :68 — fn — `Graphics::setSystemMouseCursorPosition`
- `0x00754E40` — :70 — fn — `Graphics::resize`
- `0x00755520` — :71 — fn — `Graphics::flushResources`
- `0x00764B70` — :73 — fn — `TextureList::reloadTextures`
- `0x00755910` — :75 — fn — `Graphics::setStaticShader`
- `0x00755D30` — :76 — fn — `Graphics::setObjectToWorldTransformAndScale`
- `0x00759A70` — :77 — fn — `Graphics::drawExtent`
- `0x00755890` — :79 — fn — `Graphics::screenshot`
- `0x01922E64` — :168 — data — render target width
- `0x01922E60` — :173 — data — render target height

### `UtinniCore/swg/graphics/directx9.cpp`
- `0x62A4F9DB` — :66 — fn — `D3DXCompileShader` in `s207_r.dll` (third-party DLL, NOT SWG)

### `UtinniCore/swg/graphics/post_processing.cpp`
- `0x0064B500` — :32 — fn — `PostProcessing::preSceneRender`
- `0x0064B560` — :33 — fn — `PostProcessing::postSceneRender`

### `UtinniCore/swg/graphics/shader.cpp`
- `0x00772D60` — :42 — fn — cell pop helper
- `0x00773E39` — :43 — patch — cell pop hook start
- `0x00773E41` — :44 — ret — cell pop hook return

---

## Object / Network

### `UtinniCore/swg/object/object.cpp`
- `0x00B28700` — :44 — fn — `ObjectTemplate::getByFilename`
- `0x00B28720` — :45 — fn — `ObjectTemplate::getByIff`
- `0x00B28740` — :46 — fn — `ObjectTemplate::getByCrc`
- `0x00B289B0` — :48 — fn — `ObjectTemplate::reload`
- `0x00B28A10` — :50 — fn — `ObjectTemplate::getCrcStringByName`
- `0x00B28AA0` — :51 — fn — `ObjectTemplate::getCrcStringByCrc`
- `0x00B2E760` — :58 — fn — `ObjectTemplate::createObject`
- `0x011A6C10` — :69 — fn — `Object::getAppearanceFilename`
- `0x011A6D30` — :70 — fn — `Object::getPortalLayoutFilename`
- `0x011A6E50` — :71 — fn — `Object::getClientDataFilename`
- `0x011A8B60` — :73 — fn — `Object::getGameObjectType`
- `0x01231910` — :81 — fn — `Object::getTerrainLayerFilename`
- `0x01231A30` — :82 — fn — `Object::getInteriorLayoutFilename`
- `0x00B21B80` — :132 — fn — `Object` ctor
- `0x00B222D0` — :134 — fn — `Object::isActive` (written `0xB222D0` in source)
- `0x00B23C60` — :138 — fn — `Object::getType`
- `0x00B22C30` — :140 — fn — `Object::setParentCell`
- `0x00B225F0` — :142 — fn — `Object::addToWorld`
- `0x00B22680` — :143 — fn — `Object::removeFromWorld`
- `0x00B23960` — :145 — fn — `Object::move`
- `0x00B22C80` — :147 — fn — `Object::getTransform_o2w`
- `0x00B22CC0` — :148 — fn — `Object::setTransform_o2w`
- `0x00B22E90` — :149 — fn — `Object::getTransform_a2w`
- `0x00B22E10` — :150 — fn — `Object::setTransform_a2w`
- `0x00B243F0` — :152 — fn — `Object::getPosition`
- `0x00B23960` — :153 — fn — `Object::setPosition`
- `0x00B23A10` — :155 — fn — `Object::setScale`
- `0x004361F0` — :157 — fn — `Object::rotate_o2w`
- `0x00B22FF0` — :159 — fn — `Object::getAppearance`
- `0x00B22F60` — :160 — fn — `Object::setAppearance`
- `0x00B243E0` — :161 — fn — `Object::getAppearanceFilename`
- `0x00B243A0` — :162 — fn — `Object::setAppearanceByFilename`
- `0x00B225A0` — :164 — fn — `Object::addNotification`
- `0x00B225D0` — :165 — fn — `Object::removeNotification`
- `0x00B22C00` — :167 — fn — `Object::getParentCell`
- `0x00B24CE0` — :169 — fn — `Object::setObjectToWorldDirty`
- `0x00B22A50` — :171 — fn — `Object::positionAndRotationChanged`
- `0x00554BC0` — :173 — fn — `Object::getClientObject`
- `0x00B23C40` — :175 — fn — `Object::getTemplateFilename`

### `UtinniCore/swg/object/client_object.cpp`
- `0x00555410` — :42 — fn — `ClientObject::setParentCell`
- `0x00555070` — :43 — fn — `ClientObject::beginBaselines`
- `0x00555070` — :44 — fn — `ClientObject::endBaselines`
- `0x00557360` — :46 — fn — `ClientObject::getGameObjectType`
- `0x00557370` — :47 — fn — `ClientObject::getGameObjectTypeStringIdKey`
- `0x00557390` — :48 — fn — `ClientObject::getGameObjectTypeName`
- `0x00554BF0` — :50 — fn — `ClientObject::getStaticObject`
- `0x00554C00` — :51 — fn — `ClientObject::getTangibleObject`
- `0x0070DBB0` — :60 — fn — `TangibleObject` ctor
- `0x0070DD00` — :62 — fn — `TangibleObject::addToWorld`
- `0x0070DD20` — :63 — fn — `TangibleObject::removeFromWorld`

### `UtinniCore/swg/object/creature_object.cpp`
- `0x00434AB0` — :33 — fn — `CreatureObject::setTarget`

### `UtinniCore/swg/object/player_object.cpp`
- `0x0062A8B0` — :34 — fn — `PlayerObject::teleportPlayer`
- `0x0191BFB4` — :59 — data — player object pointer (+0x674 state offset)

### `UtinniCore/swg/misc/network.cpp`
- `0x00B380E0` — :38 — fn — `IdManager::getObjectById`
- `0x00B37F30` — :39 — fn — `IdManager::getInstance`
- `0x00B30160` — :42 — fn — `CachedNetworkId::getObject`
- `0x00AA4900` — :44 — fn — `NetworkId::cast` (written `0xAA4900` in source)

---

## Appearance

### `UtinniCore/swg/appearance/appearance.cpp`
- `0x00B262A0` — :34 — fn — `SkeletalAppearance::createAppearance`
- `0x00B2C410` — :35 — fn — `SkeletalAppearance::collide`
- `0x007A85A0` — :43 — fn — `ShaderPrimitive` ctor
- `0x007A8A50` — :44 — fn — `ShaderPrimitive::render`
- `0x01922F8C` — :94 — data — static shader data ptr
- `0x01945AD4` — :95 — data — static Transform for rendering
- `0x0194596C` — :95 — data — static Vector for rendering
- `0x01945A0C` — :96 — data — static Extent for rendering

### `UtinniCore/swg/appearance/extent.cpp`
- `0x0126AF70` — :32 — fn — `Extent::intersect` (variant 1)
- `0x0126AFB0` — :33 — fn — `Extent::intersect` (variant 3)
- `0x0125FA10` — :45 — fn — `Extent::intersect` (variant 2)

### `UtinniCore/swg/appearance/portal.cpp`
- `0x00B47BD0` — :33 — fn — `PortalProperty::getCrc`
- `0x00B47BE0` — :34 — fn — `PortalProperty::getCellCount`
- `0x00B47C90` — :35 — fn — `PortalProperty::getExteriorAppearanceName`
- `0x00B497E0` — :41 — fn — `PortalProperty::getPobByCrcString`
- `0x00B22C00` — :49 — fn — `Object::getParentCell` (reused)
- `0x00B2A990` — :50 — fn — `PortalProperty::setPortalTransitions`

### `UtinniCore/swg/appearance/skeleton.cpp`
- `0x007E6C50` — :32 — fn — `SkeletalShaderPrimitive::addShaderPrimitives`
- `0x007C8B60` — :40 — fn — `SkeletalShaderPrimitive::render`
- `0x007CA130` — :41 — fn — `SkeletalShaderPrimitive::getDisplayLodSkeleton`

---

## Scene

### `UtinniCore/swg/scene/ground_scene.cpp`
- `0x00519830` — :51 — fn — `GroundScene` ctor
- `0x0051A4F0` — :52 — fn — `Terrain::reloadTerrain`
- `0x0051A350` — :53 — fn — `GroundScene::changeCamera`
- `0x0051A4D0` — :54 — fn — `GroundScene::getCurrentCamera`
- `0x0051B770` — :56 — fn — `GroundScene::draw`
- `0x0051AF10` — :57 — fn — `GroundScene::update`
- `0x0051AB20` — :58 — fn — `GroundScene::handleInputMapUpdate`
- `0x0051AA40` — :59 — fn — `GroundScene::handleInputMapEvent`
- `0x00518EB0` — :61 — fn — `GroundScene::init`
- `0x0190885C` — :73 — data — GroundScene pointer
- `0x019136E4` — :232,279 — data — scene notification callback

### `UtinniCore/swg/scene/client_world.cpp`
- `0x00561350` — :33 — fn — `ClientWorld::collide`
- `0x00562940` — :34 — fn — `ClientWorld::internalCollide`
- `0x00562680` — :35 — fn — `ClientWorld::internalCollideFindAllObjects`
- `0x0199CB34` — :42 — data — collision parameter structure

### `UtinniCore/swg/scene/render_world.cpp`
- `0x00765C20` — :34 — fn — `RenderWorld::clearVisibleCells` (written `0x765C20`)
- `0x007664F0` — :35 — fn — `RenderWorld::addObjectNotifications`
- `0x00766DE0` — :36 — fn — `RenderWorld::render`

### `UtinniCore/swg/scene/terrain.cpp`
- `0x0051A4F0` — :34 — fn — `Terrain::reloadTerrain`
- `0x00B5CBD0` — :35 — fn — `Terrain::setTimeOfDay`
- `0x00B5CBC0` — :36 — fn — `Terrain::getTimeOfDay`
- `0x00845C90` — :37 — fn — `Terrain::setWeatherIndex`
- `0x01947194` — :44 — data — Terrain object pointer
- `0x01924B6C` — :74 — data — weather index pointer
- `0x019113C1` — :84 — data — terrain filename pointer

### `UtinniCore/swg/scene/world_snapshot.cpp`
- `0x00B97D90` — :52 — fn — `WorldSnapshotReaderWriter::openFile`
- `0x00B98120` — :53 — fn — `WorldSnapshotReaderWriter::saveFile`
- `0x00B98290` — :54 — fn — `WorldSnapshotReaderWriter::clear`
- `0x00B98720` — :56 — fn — `WorldSnapshotReaderWriter::getObjectTemplateName`
- `0x00B986A0` — :58 — fn — `WorldSnapshotReaderWriter::nodeCount`
- `0x00B986D0` — :59 — fn — `WorldSnapshotReaderWriter::nodeCountTotal`
- `0x00B98740` — :61 — fn — `WorldSnapshotReaderWriter::getNodeByNetworkId`
- `0x00B986B0` — :62 — fn — `WorldSnapshotReaderWriter::getNodeByIndex`
- `0x00B98410` — :63 — fn — `WorldSnapshotReaderWriter::addNode`
- `0x00B98780` — :64 — fn — `WorldSnapshotReaderWriter::removeNode`
- `0x00B971D0` — :74 — fn — `WorldSnapshotReaderWriter::getNodeNetworkId`
- `0x00B97390` — :75 — fn — `WorldSnapshotReaderWriter::getNodeSpatialSubdivisionHandle`
- `0x00B973A0` — :76 — fn — `WorldSnapshotReaderWriter::setNodeSpatialSubdivisionHandle`
- `0x00B97440` — :78 — fn — `WorldSnapshotReaderWriter::removeFromWorld`
- `0x0059C380` — :95 — fn — `WorldSnapshot::load`
- `0x0059C1D0` — :96 — fn — `WorldSnapshot::unload`
- `0x00404D50` — :98 — fn — `WorldSnapshot::clearPreloadList`
- `0x0059BBA0` — :100 — fn — `WorldSnapshot::createObject`
- `0x0059BF20` — :101 — fn — `WorldSnapshot::addObject`
- `0x0059DC30` — :103 — fn — `WorldSnapshot::detailLevelChanged`
- `0x01913E94` — :108 — data — WorldSnapshotReaderWriter pointer
- `0x005A25A0` — :308 — fn — Void1 helper
- `0x005A08D0` — :309 — fn — Void1 helper
- `0x005A09C0` — :310 — fn — Void3 helper
- `0x005A2D90` — :311 — fn — Void2 helper
- `0x019BB7DC` — :326 — data — static flag byte
- `0x019BB7E0` — :330 — data — static object pointer
- `0x0059C3F3` — :410 — patch — NOP filename grab
- `0x0191113C` — :460 — data — preload snapshot flag

---

## UI — Controls

### `UtinniCore/swg/ui/controls/ui_base_object.cpp`
- `0x010F2A00` — :31 — fn — `UIBaseObject` ctor

### `UtinniCore/swg/ui/controls/ui_button.cpp`
- `0x011149E0` — :31 — fn — `UIButton` ctor

### `UtinniCore/swg/ui/controls/ui_cursor.cpp`
- `0x0112C630` — :31 — fn — `UICursor` ctor

### `UtinniCore/swg/ui/controls/ui_cursor_set.cpp`
- `0x0116A360` — :31 — fn — `UICursorSet` ctor

### `UtinniCore/swg/ui/controls/ui_data.cpp`
- `0x01133130` — :31 — fn — `UIData` ctor

### `UtinniCore/swg/ui/controls/ui_dropdownbox.cpp`
- `0x0117F540` — :31 — fn — `UIDropdownBox` ctor

### `UtinniCore/swg/ui/controls/ui_grid.cpp`
- `0x0117B990` — :31 — fn — `UIGrid` ctor

### `UtinniCore/swg/ui/controls/ui_list.cpp`
- `0x011388F0` — :31 — fn — `UIList` ctor

### `UtinniCore/swg/ui/controls/ui_listbox.cpp`
- `0x011369A0` — :31 — fn — `UIListbox` ctor

### `UtinniCore/swg/ui/controls/ui_page.cpp`
- `0x010FD200` — :31 — fn — `UIPage` ctor

### `UtinniCore/swg/ui/controls/ui_pie.cpp`
- `0x01134080` — :31 — fn — `UIPie` ctor

### `UtinniCore/swg/ui/controls/ui_progressbar.cpp`
- `0x0117E860` — :31 — fn — `UIProgressBar` ctor

### `UtinniCore/swg/ui/controls/ui_sliderplane.cpp`
- `0x0117D600` — :31 — fn — `UISliderPlane` ctor

### `UtinniCore/swg/ui/controls/ui_table.cpp`
- `0x0113E510` — :31 — fn — `UITable` ctor

### `UtinniCore/swg/ui/controls/ui_tab_set.cpp`
- `0x0117AC30` — :31 — fn — `UITabSet` ctor

### `UtinniCore/swg/ui/controls/ui_text.cpp`
- `0x0110ED20` — :31 — fn — `UIText` ctor

### `UtinniCore/swg/ui/controls/ui_textbox.cpp`
- `0x0112CFC0` — :32 — fn — `UITextbox` ctor
- `0x01120250` — :33 — fn — `UITextbox::setLocalText`

### `UtinniCore/swg/ui/controls/ui_tree_view.cpp`
- `0x011549C0` — :31 — fn — `UITreeView` ctor

### `UtinniCore/swg/ui/controls/ui_unknown.cpp`
- `0x01167510` — :31 — fn — `UIUnknown` ctor

### `UtinniCore/swg/ui/controls/ui_widget.cpp`
- `0x01105910` — :31 — fn — `UIWidget` ctor

---

## UI — CUI

### `UtinniCore/swg/ui/command_parser.cpp`
- `0x00A83EF0` — :35 — fn — `CommandParser` ctor variant 1
- `0x00A84130` — :36 — fn — `CommandParser` ctor variant 2
- `0x00A862F0` — :38 — fn — `CommandParser::createDelegateCommands`
- `0x00A85CD0` — :39 — fn — `CommandParser::addSubCommand`

### `UtinniCore/swg/ui/cui_chat_window.cpp`
- `0x00F364B0` — :36 — fn — `CuiChatWindow` ctor
- `0x00F38500` — :37 — fn — `CuiChatWindow::enableTextInput`
- `0x00F3BFD0` — :38 — fn — `CuiChatWindow::writeToAllTabs`
- `0x00F3C1F0` — :39 — fn — `CuiChatWindow::writeToCurrentTab`
- `0x009141D0` — :45 — fn — `CuiChatWindow::sendInput`
- `0x00914245` — :98 — patch
- `0x00914250` — :99 — patch
- `0x0091425D` — :100 — patch
- `0x0091427D` — :101 — patch
- `0x009142E4` — :102 — patch
- `0x0091428C` — :104,116 — patch — set to 0x75 / 0x74
- `0x00F3679D` — :141 — ret — return from ctor hook
- `0x00F36797` — :168 — patch — hook installation

### `UtinniCore/swg/ui/cui_hud.cpp`
- `0x00BD56F0` — :38 — fn — `CuiHud::update`
- `0x00EDBAA0` — :39 — fn — `CuiAction::performAction`
- `0x00BD3E20` — :40 — fn — `CuiHud::getTarget`
- `0x019488C8` — :70 — data — view distance float
- `0x00BD5961` — :104 — patch — mid-update hook
- `0x00BD595C` — :105 — ret
- `0x00BD3FA3` — :143,148 — patch
- `0x00BD403D` — :143 — patch — jump target

### `UtinniCore/swg/ui/cui_io.cpp`
- `0x0093BD50` — :36 — fn — `CuiIo::processEvent` (written `0x093BD50`)
- `0x0093D490` — :37 — fn — `CuiIo::setKeyboardInputActive`
- `0x0093D560` — :38 — fn — `CuiIo::requestKeyboard`
- `0x0093B2B0` — :39 — fn — `CuiIo::draw`
- `0x0192613C` — :57 — data — CuiIo pointer

### `UtinniCore/swg/ui/cui_manager.cpp`
- `0x00881210` — :39 — fn — `CuiManager::render`
- `0x00BD3E20` — :40 — fn — `CuiManager::findObjectUnderCursor`
- `0x00882410` — :42 — fn — `CuiManager::setSize`
- `0x00881940` — :43 — fn — `CuiManager::togglePointer`
- `0x00881560` — :45 — fn — `CuiManager::restartMusic`
- `0x010E8410` — :52 — fn — `CuiManager::drawCursor`
- `0x008ABEB0` — :61 — fn — `CuiManager::receiveMessage`
- `0x008AC250` — :62 — fn — `CuiManager::sendMessage`
- `0x01996E98` — :122 — data — UiManager pointer

### `UtinniCore/swg/ui/cui_menu.cpp`
- `0x00A08EE0` — :33 — fn — `InfoTypes::findDefaultCursor`

### `UtinniCore/swg/ui/cui_misc.cpp`
- `0x00BAA7E0` — :33 — fn — `SwgCuiHudFactory::reloadUi`
- `0x00C8CE00` — :42 — fn — `CuiMiscFlagsWindow` ctor
- `0x00C8D190` — :43 — fn — `CuiMiscFlagsWindow::activate`
- `0x00C8D5D0` — :44 — fn — `CuiMiscFlagsWindow::login`
- `0x01926138` — :53 — data — misc flag
- `0x00C8D250` — :62 — patch — location button
- `0x00C7D57F` — :69 — patch — buffer location
- `0x009CC385` — :73 — patch — RESO.Y changing CUI.X
- `0x009CC39C` — :74 — patch — RESO.Y changing CUI.Y
- `0x009CC3BD` — :75 — patch — isOk bool

### `UtinniCore/swg/ui/cui_radial_menu.cpp`
- `0x009698C0` — :33 — fn — `CuiRadialMenu::update`
- `0x0096C550` — :34 — fn — `CuiRadialMenu::clear`

---

## Misc

### `UtinniCore/swg/misc/audio.cpp`
- `0x00412C20` — :30 — fn — `Audio::setMasterVolume`
- `0x00412C70` — :33 — fn — `Audio::getMasterVolume`

### `UtinniCore/swg/misc/config.cpp`
- `0x00A9C6C0` — :37 — fn — `ConfigFile::loadBuffer`
- `0x00A9C780` — :38 — fn — `ConfigFile::loadString`
- `0x00401000` — :39 — fn — `ConfigFile::loadOverrideConfig`
- `0x00910A70` — :41 — fn — `CuiChatManager::setModalChat`
- `0x00910D40` — :42 — fn — `CuiChatManager::getModalChat`
- `0x01911218` — :89 — data — `avatarSelection` config pointer
- `0x01911240` — :94 — data — `groundScene` config pointer

### `UtinniCore/swg/misc/crc_string.cpp`
- `0x00AA55B0` — :33 — fn — `CrcString(const char*)` ctor
- `0x00AA4050` — :34 — fn — `PersistentCrcString(const char*)` ctor

### `UtinniCore/swg/misc/direct_input.cpp`
- `0x00420880` — :35 — fn — `DirectInput::suspend`
- `0x00420890` — :36 — fn — `DirectInput::resume`
- `0x00421490` — :38 — fn — `DirectInput::setupInstall`
- `0x0193C5E0` — :70 — data — HCURSOR pointer

### `UtinniCore/swg/misc/io_win.cpp`
- `0x00AB58E0` — :31 — fn — `IoWin::draw`
- `0x00AA6660` — :41 — fn — `IoWin::getCount`
- `0x00AA63B0` — :42 — fn — `IoWin::getMessage`
- `0x00AA6640` — :43 — fn — `IoWin::appendMessage`
- `0x00AA6480` — :44 — fn — `IoWin::appendMessageData`

### `UtinniCore/swg/misc/swg_math.cpp`
- `0x00AB5C40` — :34 — fn — `VectorMath::vectorNormalize`

### `UtinniCore/swg/misc/swg_memory.cpp`
- `0x00AC15C0` — :35 — fn — `MemoryManager::allocate`
- `0x012EA770` — :36 — fn — `MemoryManager::allocateString`
- `0x00AC1640` — :38 — fn — `MemoryManager::deallocate`
- `0x012EA920` — :39 — fn — `MemoryManager::deallocateString`

### `UtinniCore/swg/misc/swg_misc.cpp`
- `0x00A88F90` — :31 — fn — `Printf` (logging)

### `UtinniCore/swg/misc/swg_utility.cpp`
- `0x00AA4790` — :32 — fn — `Crc::calculate`
- `0x00A931E0` — :33 — fn — `TreeFile::open`

### `UtinniCore/swg/misc/tree_file.cpp`
- `0x00A992E0` — :32 — fn — `TreeFile::search` (written `0xA992E0`)

---

## Managed (C#) interop

### `UtinniCoreDotNet/UI/Controls/PanelGame.cs`
- `0x00AA0970` — :40 — fn — SWG's `WndProc` (duplicate of `client.cpp:43`)

---

## Notes

- Several addresses in source are written without leading `0x00` zero-pad (`0xAA4900`, `0xA992E0`, `0xB222D0`, `0x765C20`, `0x772D60`, `0x093BD50`). Same value, just easy to miss in grep.
- `0x62A4F9DB` in `directx9.cpp` is inside `s207_r.dll`, **not** the SWG client EXE — exclude from any rebasing analysis.
- Static data pointers cluster in `0x019xxxxx`–`0x01Axxxxx` (SWG's `.data`); function entry points cluster in `0x004xxxxx`–`0x012xxxxx` (`.text`, several compilation units).
