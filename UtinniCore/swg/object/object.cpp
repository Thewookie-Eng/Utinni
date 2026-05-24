/**
 * MIT License
 *
 * Copyright (c) 2020 Philip Klatt
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
**/


#include "object.h"
#include "swg/appearance/appearance.h"
#include "swg/misc/swg_math.h"
#include "swg/misc/network.h"
#include "swg/misc/swg_memory.h"
#include "swg/misc/swg_utility.h"

namespace swg::objectTemplateList
{
using pGetObjectTemplateByFilename = utinni::SharedObjectTemplate* (__cdecl*)(const char* filename);
using pGetObjectTemplateByIff = utinni::SharedObjectTemplate* (__cdecl*)(swgptr iff);
using pGetObjectTemplateByCrc = utinni::SharedObjectTemplate* (__cdecl*)(unsigned int crc);

using pReloadObject = swgptr(__cdecl*)(swgptr iff);

using pGetCrcStringByName = utinni::ConstCharCrcString(__cdecl*)(utinni::ConstCharCrcString* result, const char* name);
using pGetCrcStringByCrc = swgptr(__cdecl*)(void* result, unsigned int crc);

pGetObjectTemplateByFilename getObjectTemplateByFilename = (pGetObjectTemplateByFilename)addresses::swg::objectTemplateList::getObjectTemplateByFilename;
pGetObjectTemplateByIff getObjectTemplateByIff = (pGetObjectTemplateByIff)addresses::swg::objectTemplateList::getObjectTemplateByIff;
pGetObjectTemplateByCrc getObjectTemplateByCrc = (pGetObjectTemplateByCrc)addresses::swg::objectTemplateList::getObjectTemplateByCrc;

pReloadObject reloadObject = (pReloadObject)addresses::swg::objectTemplateList::reloadObject;

pGetCrcStringByName getCrcStringByName = (pGetCrcStringByName)addresses::swg::objectTemplateList::getCrcStringByName;
pGetCrcStringByCrc getCrcStringByCrc = (pGetCrcStringByCrc)addresses::swg::objectTemplateList::getCrcStringByCrc;
}

namespace swg::objectTemplate
{
using pCreateObject = utinni::Object* (__cdecl*)(const char* filename);

pCreateObject createObject = (pCreateObject)addresses::swg::objectTemplate::createObject;
}

namespace swg::sharedObjectTemplate
{
using pGetAppearancetFilename = const char** (__thiscall*)(utinni::SharedObjectTemplate* pThis, bool unk);
using pGetPortalLayoutFilename = const char** (__thiscall*)(utinni::SharedObjectTemplate* pThis, bool unk);
using pGetClientDataFilename = const char** (__thiscall*)(utinni::SharedObjectTemplate* pThis, bool unk);

using pGetGameObjectType = int(__thiscall*)(utinni::SharedObjectTemplate* pThis, bool unk);

pGetAppearancetFilename getAppearancetFilename = (pGetAppearancetFilename)addresses::swg::sharedObjectTemplate::getAppearancetFilename;
pGetPortalLayoutFilename getPortalLayoutFilename = (pGetPortalLayoutFilename)addresses::swg::sharedObjectTemplate::getPortalLayoutFilename;
pGetClientDataFilename getClientDataFilename = (pGetClientDataFilename)addresses::swg::sharedObjectTemplate::getClientDataFilename;

pGetGameObjectType getGameObjectType = (pGetGameObjectType)addresses::swg::sharedObjectTemplate::getGameObjectType;
}

namespace swg::sharedBuildingObjectTemplate
{
using pGetTerrainLayerFilename = const char* (__thiscall*)(utinni::SharedBuildingObjectTemplate* pThis, bool unk);
using pGetInteriorLayoutFilename = const char* (__thiscall*)(utinni::SharedBuildingObjectTemplate* pThis, bool unk);

pGetTerrainLayerFilename getTerrainLayerFilename = (pGetTerrainLayerFilename)addresses::swg::sharedBuildingObjectTemplate::getTerrainLayerFilename;
pGetInteriorLayoutFilename getInteriorLayoutFilename = (pGetInteriorLayoutFilename)addresses::swg::sharedBuildingObjectTemplate::getInteriorLayoutFilename;
}

namespace swg::object
{
using pCtor = utinni::Object* (__thiscall*)(utinni::Object* pThis);

using pIsActive = bool (__thiscall*)(utinni::Object* pThis);

using pDisallowDelete = void(__cdecl*)(bool disallowDelete);

using pGetType = unsigned int(__thiscall*)(utinni::Object* pThis);

using pSetParentCell = void(__thiscall*)(utinni::Object* pThis, DWORD parentCell);

using pAddToWorld = void(__thiscall*)(utinni::Object* pThis);
using pRemoveFromWorld = void(__thiscall*)(utinni::Object* pThis);

using pMove = void(__thiscall*)(utinni::Object* pThis, const swg::math::Vector& vector);

using pGetTransform_o2w = swg::math::Transform* (__thiscall*)(utinni::Object* pThis);
using pSetTransform_o2w = void(__thiscall*)(utinni::Object* pThis, swg::math::Transform& objectToWorld);
using pGetTransform_a2w = swg::math::Transform* (__thiscall*)(utinni::Object* pThis);
using pSetTransform_a2w = void(__thiscall*)(utinni::Object* pThis, swg::math::Transform& appearanceToWorld);

using pGetPosition = swg::math::Vector* (__thiscall*)(utinni::Object* pThis);
using pSetPosition = void(__thiscall*)(utinni::Object* pThis, swg::math::Vector& position);

using pSetScale = void(__thiscall*)(utinni::Object* pThis, swg::math::Vector& scale);

using pRotate_o2w = const swg::math::Vector(__thiscall*)(utinni::Object* pThis, DWORD unk, const swg::math::Vector* o2w, const swg::math::Vector* pointInSpace); // ??

using pGetAppearance = utinni::Appearance* (__thiscall*)(utinni::Object* pThis);
using pSetAppearance = void(__thiscall*)(utinni::Object* pThis, utinni::Appearance* appearance);
using pGetAppearanceFilename = const char* (__thiscall*)(utinni::Object* pThis);
using pSetAppearanceByFilename = void(__thiscall*)(utinni::Object* pThis, const char* filename);

using pAddNotification = void(__thiscall*)(utinni::Object* pThis, swgptr notification, bool allowInWorld);
using pRemoveNotification = void(__thiscall*)(utinni::Object* pThis, swgptr notification, bool allowInWorld);

using pGetParentCell = utinni::CellProperty* (__thiscall*)(utinni::Object* pThis);

using pSetObjectToWorldDirty = void(__thiscall*)(utinni::Object* pThis, bool isDirty);

using pPositionAndRotationChanged = void(__thiscall*)(utinni::Object* pThis, bool dueToParentChange, swg::math::Vector& oldPosition);

using pGetClientObject = utinni::ClientObject*(__thiscall*)(utinni::Object* pThis);

using pGetTemplateFilename = const char* (__thiscall*)(utinni::Object* pThis);

pCtor ctor = (pCtor)addresses::swg::object::ctor;

pIsActive isActive = (pIsActive)addresses::swg::object::isActive;

pDisallowDelete disallowDelete;

pGetType getType = (pGetType)addresses::swg::object::getType;

pSetParentCell setParentCell = (pSetParentCell)addresses::swg::object::setParentCell;

pAddToWorld addToWorld = (pAddToWorld)addresses::swg::object::addToWorld;
pRemoveFromWorld removeFromWorld = (pRemoveFromWorld)addresses::swg::object::removeFromWorld;

pMove move = (pMove)addresses::swg::object::move;

pGetTransform_o2w getTransform_o2w = (pGetTransform_o2w)addresses::swg::object::getTransform_o2w;
pSetTransform_o2w setTransform_o2w = (pSetTransform_o2w)addresses::swg::object::setTransform_o2w;
pGetTransform_a2w getTransform_a2w = (pGetTransform_a2w)addresses::swg::object::getTransform_a2w;
pSetTransform_a2w setTransform_a2w = (pSetTransform_a2w)addresses::swg::object::setTransform_a2w;

pGetPosition getPosition = (pGetPosition)addresses::swg::object::getPosition;
pSetPosition setPosition = (pSetPosition)addresses::swg::object::setPosition;

pSetScale setScale = (pSetScale)addresses::swg::object::setScale;

pRotate_o2w rotate_o2w = (pRotate_o2w)addresses::swg::object::rotate_o2w;

pGetAppearance getAppearance = (pGetAppearance)addresses::swg::object::getAppearance;
pSetAppearance setAppearance = (pSetAppearance)addresses::swg::object::setAppearance;
pGetAppearanceFilename getAppearanceFilename = (pGetAppearanceFilename)addresses::swg::object::getAppearanceFilename;
pSetAppearanceByFilename setAppearanceByFilename = (pSetAppearanceByFilename)addresses::swg::object::setAppearanceByFilename;

pAddNotification addNotification = (pAddNotification)addresses::swg::object::addNotification;
pRemoveNotification removeNotification = (pRemoveNotification)addresses::swg::object::removeNotification;

pGetParentCell getParentCell = (pGetParentCell)addresses::swg::object::getParentCell;

pSetObjectToWorldDirty setObjectToWorldDirty = (pSetObjectToWorldDirty)addresses::swg::object::setObjectToWorldDirty;

pPositionAndRotationChanged positionAndRotationChanged = (pPositionAndRotationChanged)addresses::swg::object::positionAndRotationChanged;

pGetClientObject getClientObject = (pGetClientObject)addresses::swg::object::getClientObject;

pGetTemplateFilename getTemplateFilename = (pGetTemplateFilename)addresses::swg::object::getTemplateFilename;
}

namespace utinni
{
SharedObjectTemplate* ObjectTemplateList::getObjectTemplateByFilename(const char* filename)
{
    return swg::objectTemplateList::getObjectTemplateByFilename(filename);
}

SharedObjectTemplate* ObjectTemplateList::getObjectTemplateByIff(swgptr iff)
{
    return swg::objectTemplateList::getObjectTemplateByIff(iff);
}

ConstCharCrcString getCrcStringByCrc(unsigned int crc)
{
    return *(ConstCharCrcString*)swg::objectTemplateList::getCrcStringByCrc(allocate(sizeof(ConstCharCrcString)), crc);
}

ConstCharCrcString ObjectTemplateList::getCrcStringByName(const char* name)
{
    return *(ConstCharCrcString*)swg::objectTemplateList::getCrcStringByCrc(allocate(sizeof(ConstCharCrcString)), calculateCrc(name));
}

swgptr ObjectTemplateList::getCrcStringByNameAsPtr(const char* name)
{
    return swg::objectTemplateList::getCrcStringByCrc(allocate(sizeof(ConstCharCrcString)), calculateCrc(name));
}

Object* ObjectTemplate::createObject(const char* filename)
{
    return swg::objectTemplate::createObject(filename);
}

const char* SharedObjectTemplate::getAppearanceFilename()
{
    return *swg::sharedObjectTemplate::getAppearancetFilename(this, false);
}

const char* SharedObjectTemplate::getPortalLayoutFilename()
{
    return *swg::sharedObjectTemplate::getPortalLayoutFilename(this, false);
}

const char* SharedObjectTemplate::getClientDataFilename()
{
    return *swg::sharedObjectTemplate::getClientDataFilename(this, false);
}

int SharedObjectTemplate::getGameObjectType()
{
    return swg::sharedObjectTemplate::getGameObjectType(this, false);
}

const char* SharedBuildingObjectTemplate::getTerrainLayerFilename()
{
    return swg::sharedBuildingObjectTemplate::getTerrainLayerFilename(this, false);
}

const char* SharedBuildingObjectTemplate::getInteriorLayoutFilename()
{
    return swg::sharedBuildingObjectTemplate::getInteriorLayoutFilename(this, false);
}

Object* Object::ctor()
{
    return swg::object::ctor((Object*)allocate(160));
}

Object* Object::getObjectById(swgptr cachedNetworkId)
{
    if (cachedNetworkId == 0)
    {
        return nullptr;
    }

    return Network::getCachedObjectById(cachedNetworkId);
}

void Object::remove()
{
    (**(void(__thiscall***)(Object*, bool))this)(this, true); // ToDo do this proper at some point, taken from IDA pseudo code
}

bool Object::isActive()
{
    return swg::object::isActive(this);
}

swg::math::Transform* Object::getTransform()
{
    if (parentObject == nullptr)
    {
        return getTransform_o2w();
    }
    else
    {
        return &objectToParent;
    }
}

swg::math::Transform* Object::getTransform_o2w()
{
    return swg::object::getTransform_o2w(this);
}

void Object::setTransform_o2w(swg::math::Transform& object2world)
{
    swg::object::setTransform_o2w(this, object2world);
}

const swg::math::Vector Object::rotate_o2w(const swg::math::Vector* o2w, const swg::math::Vector* pointInSpace)
{
    return swg::object::rotate_o2w(this, 0, o2w, pointInSpace);
}

void Object::move(const swg::math::Vector& vector)
{
    swg::object::move(this, vector);
}

void Object::addNotification(swgptr notification, bool allowWhenInWorld)
{
    swg::object::addNotification(this, notification, allowWhenInWorld);
}

void Object::removeNotification(swgptr notification, bool allowWhenInWorld)
{
    swg::object::removeNotification(this, notification, allowWhenInWorld);
}

void Object::addToWorld()
{
    swg::object::addToWorld(this);
}

void Object::removeFromWorld()
{
    swg::object::removeFromWorld(this);
}

void Object::setAppearance(Appearance* appearance)
{
    swg::object::setAppearance(this, appearance);
}

CellProperty* Object::getParentCell()
{
    return swg::object::getParentCell(this);
}

void Object::setObjectToWorldDirty(bool isDirty)
{
    swg::object::setObjectToWorldDirty(this, isDirty);
}

void Object::positionAndRotationChanged(bool dueToParentChange, swg::math::Vector& oldPosition)
{
    swg::object::positionAndRotationChanged(this, dueToParentChange, oldPosition);
}

ClientObject* Object::getClientObject()
{
    return swg::object::getClientObject(this);
}

const char* Object::getTemplateFilename()
{
    return swg::object::getTemplateFilename(this);
}

const char* Object::getAppearanceFilename()
{
    return swg::object::getAppearanceFilename(this);
}
}
