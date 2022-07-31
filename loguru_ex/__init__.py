#!/usr/bin/env python
# -*- coding: UTF-8 -*-    
# Author: DoubleT.Wong
# FileName: __init__.py
# DateTime: 7/26/2022 7:32 PM
import os.path
import pathlib
import inspect
import yaml

from loguru import logger
from os import PathLike
from typing import Union, Dict, List, Callable
from collections import namedtuple
from types import FrameType

_LOG_CONFIG = {
    'level': 'INFO',
    'format': '{time:YYYY-MM-DD HH:mm:ss.SSS} | '
              '{level: <8} | {file} | {name}:{function}:{line} - {message}',
    'rotation': '01:00',
    'retention': 15,
    'compression': 'zip'
}

_LOG_HANDLERS = {}


def set_global_config(config: Union[str, PathLike, Dict]) -> None:
    """
    Set global log config by a Dict or a config file,
    but only effect for new register.
    :param config: a Dict or a config file
    :return: None
    """
    if not isinstance(config, (dict, str, PathLike)):
        logger.warning(f'Parser log config failed, parameter error!')
        return
    if isinstance(config, (str, PathLike)) \
            and not os.path.exists(config):
        logger.warning(f'Parser log config failed, {config} is not exist!')
        return

    if isinstance(config, dict):
        _LOG_CONFIG.update(**config)
        return
    try:
        with open(config, encoding='utf-8') as f:
            _LOG_CONFIG.update(**yaml.safe_load(f))
    except Exception as e:
        logger.warning(f'Parser log config failed, {e}')


def _get_standard_objs(objs: Union[str, PathLike, object]) -> List[namedtuple]:
    """
    Get standard log filter objects.
    :return: a list of objects
    """
    new_objs = []
    new_obj_namedtuple = namedtuple('Filter', 'type, name, file')
    for obj in objs:
        isclass, isfunction, ismethod = False, False, False
        if isinstance(obj, str):
            file_path = pathlib.Path(obj)
            new_obj = new_obj_namedtuple('path', file_path, file_path)
        elif inspect.ismodule(obj):
            file_path = pathlib.Path(obj.__file__)
            new_obj = new_obj_namedtuple('path', file_path, file_path)
        elif (isclass := inspect.isclass(obj)) \
                or inspect.isfunction(obj) \
                or (ismethod := inspect.ismethod(obj)):
            file_path = pathlib.Path(inspect.getfile(obj))
            obj_type = 'class' if isclass else 'function'
            obj_name = obj.__name__
            if ismethod:
                obj_type = 'method'
                _class_name = obj.__self__.__class__.__name__
                obj_name = f'{_class_name}.{obj_name}'
            new_obj = new_obj_namedtuple(obj_type, obj_name, file_path)
        else:
            logger.warning(f'Init filter error, {obj} is not supported!')
            continue
        new_objs.append(new_obj)
    return new_objs


def _get_class_name(frame: FrameType, function_name: str) -> str:
    """
    Get class name by a frame.
    :param frame: a frame object of a stack
    :param function_name: a function name in this class
    :return: a class name
    """
    class_name = None
    code = frame.f_code
    if code.co_argcount > 0:
        first_arg = frame.f_locals[code.co_varnames[0]]
        if hasattr(first_arg, function_name) \
                and getattr(first_arg, function_name).__code__ is code:
            if inspect.isclass(first_arg):
                class_name = first_arg.__qualname__
            else:
                class_name = first_arg.__class__.__qualname__
    return class_name


def _is_log_passable(stack: inspect.FrameInfo, filter_objs: List[namedtuple])\
        -> bool:
    """
    Check if a stack is passable from the log filter.
    :param stack: a code stack
    :param filter_objs: a list of log filter objects
    :return: True or False
    """
    file = pathlib.Path(stack.filename)
    frame = stack.frame
    function_name = frame.f_code.co_name
    class_name = _get_class_name(frame, function_name)
    if class_name is None:
        method_name = None
    else:
        method_name = f'{class_name}.{function_name}'

    # print(f'{file=}, {function_name=}, {class_name=}, {method_name=}')
    for filter_obj in filter_objs:
        # print(filter_obj)
        if filter_obj.type == 'path':
            try:
                file.relative_to(filter_obj.file)
                return True
            except ValueError:
                pass

        if file != filter_obj.file:
            continue

        if filter_obj.type == 'method' and method_name == filter_obj.name:
            return True

        if filter_obj.type == 'function' and \
                function_name == filter_obj.name:
            return True

        if filter_obj.type == 'class' and class_name == filter_obj.name:
            return True
    # print("Didn't match any filter!")
    return False


def _get_log_filter(*objs: namedtuple) -> Callable:
    """
    Get a filter function by a list of objects.
    :param objs: a list of filter objects
    :return: a filter function
    """
    def log_filter(record):
        stacks = inspect.stack()
        # the first 4 stack is the code of loguru, don't need to check
        for stack in stacks[4:][::-1]:
            if _is_log_passable(stack, objs):
                return True
        return False

    return log_filter


def register_logger(
        log_path: Union[str, PathLike],
        *objs: Union[str, PathLike, object]
) -> None:
    """
    Register objs to log file, and then all logs of these objs can be
    outputted to this log file.
    :param log_path: path of the log file
    :param objs: a list of objs which need to be outputted to log file
    :return: None
    """
    log_path = str(pathlib.Path(log_path).absolute())
    standard_objs = _get_standard_objs(objs)
    if log_path in _LOG_HANDLERS:
        for obj in _LOG_HANDLERS[log_path]['objs']:
            if obj not in standard_objs:
                standard_objs.append(obj)
    else:
        _LOG_HANDLERS[log_path] = {'id': None}

    log_filter = _get_log_filter(*standard_objs)
    _LOG_HANDLERS[log_path]['objs'] = standard_objs

    if _LOG_HANDLERS[log_path]['id']:
        logger.remove(_LOG_HANDLERS[log_path]['id'])
    _LOG_HANDLERS[log_path]['id'] = logger.add(
        log_path,
        level=_LOG_CONFIG['level'],
        filter=log_filter,
        format=_LOG_CONFIG['format'],
        rotation=_LOG_CONFIG['rotation'],
        retention=_LOG_CONFIG['retention'],
        compression=_LOG_CONFIG['compression']
    )


def unregister_logger(
        log_path: Union[str, PathLike],
        *objs: Union[str, PathLike, object]
) -> None:
    """
    Unregister objs from log file.
    :param log_path: path of the log file
    :param objs: a list of objs which need to be outputted to log file
    :return: None
    """
    log_path = str(pathlib.Path(log_path).absolute())

    if log_path in _LOG_HANDLERS:
        if objs:
            objs = _get_standard_objs(objs)
            for obj in objs:
                if obj in _LOG_HANDLERS[log_path]['objs']:
                    _LOG_HANDLERS[log_path]['objs'].remove(obj)
            if _LOG_HANDLERS[log_path]['objs']:
                log_filter = _get_log_filter(*_LOG_HANDLERS[log_path]['objs'])
                logger.remove(_LOG_HANDLERS[log_path]['id'])
                _LOG_HANDLERS[log_path]['id'] = logger.add(
                    log_path,
                    level=_LOG_CONFIG['level'],
                    filter=log_filter,
                    format=_LOG_CONFIG['format'],
                    rotation=_LOG_CONFIG['rotation'],
                    retention=_LOG_CONFIG['retention'],
                    compression=_LOG_CONFIG['compression']
                )
            else:
                logger.remove(_LOG_HANDLERS[log_path]['id'])
                del _LOG_HANDLERS[log_path]
        else:
            logger.remove(_LOG_HANDLERS[log_path]['id'])
            del _LOG_HANDLERS[log_path]
    else:
        logger.warning(f'Log file {log_path} is not registered!')
