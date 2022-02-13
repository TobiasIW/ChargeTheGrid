#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 15 18:03:20 2021

@author: trocotronic
"""

import NativeAPI
import logging
from datetime import datetime, timedelta
import configparser
import json
import sys

logger = logging.getLogger('VWVehicle')
logger.setLevel(logging.getLogger().level)

def load_datetime(s):
    return datetime.fromisoformat(s.replace('Z','+00:00')).replace(tzinfo=None)

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

class VWVehicle:
    __api = None
    __vin = None
    __cardata = None
    __supported_services = {
        'carfinder_v1': { 'status': False },
        'trip_statistic_v1': { 'status': False },
        'rlu_v1': { 'status': False },
        'statusreport_v1': { 'status': False },
        'geofence_v1': { 'status': False },
        'speedalert_v1': { 'status': False },
        'rhonk_v1': { 'status': False },
        'rheating_v1': { 'status': False },
        'rclima_v1': { 'status': False },
        'rbatterycharge_v1': { 'status': False }
        }
    
    def __init__(self,fileconf = 'vehicle.conf'):
        self.__parse_conf(fileconf)
        self.__api = NativeAPI.WeConnect()
        self.__api.login()
        self.__discover()
        
    def __parse_conf(self, fileconf):
        self.__config = configparser.ConfigParser()
        self.__config.read(fileconf)
        self.__vin = self.__config.get('general','vin',fallback=None)
        
    def set_logging_level(self, level):
        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        for logger in loggers:
            logger.setLevel(level)
    
    def version(self):
        return self.__api.version()
    
    def __discover(self):
        realcars = self.__api.get_real_car_data().get('realCars',[])
        if (len(realcars) == 0):
            logger.critical('No cars found. Cannot continue.')
            sys.exit(-1)
        if (len(realcars) == 1 and self.__vin is None):
            self.__vin = realcars[0].get('vehicleIdentificationNumber','NO_VIN')
            self.__cardata = realcars[0]
            logger.info('Found 1 car. Setting default VIN to {}'.format(self.__vin))
        else:
            for car in realcars:
                if (car.get('vehicleIdentificationNumber','NO_VIN') == self.__vin):
                    self.__cardata = car
                    break
            if (self.__cardata):
                logger.info('Found car with VIN {}'.format(self.__vin))
            else:
                logger.critical('No car found with VIN {}. Cannot continue.'.format(self.__vin))
                sys.exit(-1)
        if (self.__cardata.get('deactivated',False)):
            logger.critical('Car {} is deactivated: {}.\nCannot continue.'.format(self.__vin, self.__cardata.get('deactivationReason','NO_REASON')))
            sys.exit(-1)
        self.__nickname = self.__cardata.get('nickname','NO_NAME')
        logger.info('Discovering services for vehicle {} ({})'.format(self.__nickname, self.__vin))
        self.__vehicledata = self.__api.get_vehicle_data(self.__vin)
        self.__api.set_brand_country(self.__vehicledata.get('vehicleDataDetail',{}).get('brand','VW'),self.__vehicledata.get('vehicleDataDetail',{}).get('country','DE'))
        self.__roles = self.__api.get_roles_rights(self.__vin).get('operationList',{})
        services = self.__roles.get('serviceInfo',[])
        for service in services:
            service_name = service.get('serviceId','NO_SERVICE')
            if (service_name in self.__supported_services.keys()):
                service_status = True if service.get('serviceStatus',{}).get('status','Disabled') == 'Enabled' else False
                logger.info('Discovered supported service {} with status {}.'.format(service_name, 'Eanbled' if service_status else 'Disabled'))
                self.__supported_services[service_name]['status'] = service_status
                if (service_status is None):
                    logger.warning('Service {} is disabled: {}'.format(service_name, service.get('serviceStatus',{}).get('reason','NO_REASON')))
                else:
                    self.__supported_services[service_name]['expiration'] = service.get('cumulatedLicense', {}).get('expirationDate', {}).get('content', None)
                    if (self.__supported_services[service_name]['expiration']):
                        logger.info('Service {} set expiration to {}'.format(service_name,self.__supported_services[service_name]['expiration']))
                    self.__supported_services[service_name]['operations'] = [op.get('id','NO_ID') for op in service.get('operation', [])]
    
    def __check_access(self,service_name):
        if (self.__supported_services.get(service_name,{}).get('status',False)):
            now = datetime.utcnow()
            expiration = load_datetime(self.__supported_services[service_name].get('expiration',(now+timedelta(weeks=1)).isoformat()))
            if (now >= expiration):
                logger.warning('Calling expired service {} (expired on {})'.format(service_name,expiration))
            return now < expiration
        return False
    
    def get_position(self):
        if (self.__check_access('carfinder_v1')):
            pos = self.__api.get_position(self.__vin)
            logger.info('Received position')
            if (self.__config.getboolean('position','record',fallback=False)):
                posfile = self.__config.get('position','file',fallback='position.history')
                logger.info('Recording position to {}'.format(posfile))
                try:
                    with open(posfile) as json_file:
                        data = json.load(json_file)
                    logger.debug('Found position file')
                except (FileNotFoundError,json.decoder.JSONDecodeError):
                    data = []
                    logger.debug('Position file not found')
                parking = load_datetime(pos.get('storedPositionResponse',{}).get('parkingTimeUTC','1970-01-01T00:00:00Z'))
                if (len(data) == 0 or load_datetime(data[-1]['timestamp']) < parking):
                    logger.debug('Updating record history with new timestamp {}'.format(parking))
                    coords = pos.get('storedPositionResponse',{}).get('position',{}).get('carCoordinate',{})
                    data.append({'timestamp': parking, 'coordinates': {'latitude': coords.get('latitude',0), 'longitude': coords.get('longitude')}})
                    with open(self.__config.get('position','file',fallback='position.history'),'w') as json_file:
                        json.dump(data, json_file, default=json_serial)
                    logger.debug('Record history updated')
                elif (load_datetime(data[-1]['timestamp']) >= parking):
                    logger.debug('No new records found. Record history not updated')
            return pos