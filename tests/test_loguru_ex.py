#!/usr/bin/env python
# -*- coding: UTF-8 -*-    
# Author: 王涛涛/16327
# FileName: test_log_utils
# DateTime: 7/30/2022 5:02 PM
import os.path
import sys
import pytest

from loguru import logger

from loguru_ex import register_logger, unregister_logger

INVALID_LOG = 'a invalid log'
logs = [f'[this is a valid log {i:>03}]' for i in range(6)]


class ClassA:

    def __init__(self, log):
        logger.info(log)

    @staticmethod
    def staticmethod_a(log):
        logger.info(log)

    def method_a(self, log):
        logger.info(log)


def function_a(log):
    logger.info(log)


class ClassB:

    def __init__(self, log):
        logger.info(log)

    @staticmethod
    def staticmethod_b(log):
        logger.info(log)

    def method_b(self, log):
        logger.info(log)


def function_b(log):
    logger.info(log)


@pytest.fixture
def log_file(request):
    case_name = request.node.name
    log_file_path = f'tmp/{case_name}.log'
    if os.path.isfile(log_file_path):
        os.remove(log_file_path)
    yield log_file_path
    if os.path.isfile(log_file_path):
        os.remove(log_file_path)


@pytest.fixture
def another_log_file(request):
    case_name = request.node.name
    log_file_path = f'tmp/another_{case_name}.log'
    if os.path.isfile(log_file_path):
        os.remove(log_file_path)
    yield log_file_path
    if os.path.isfile(log_file_path):
        os.remove(log_file_path)


class TestLogUtil:

    def test_register_a_dir(self, log_file):
        # didn't test when log from other dir
        parent_dir = os.path.dirname(__file__)
        register_logger(log_file, parent_dir)
        logger.info(logs[0])
        unregister_logger(log_file, parent_dir)
        assert os.path.isfile(log_file), f'Write {log_file} failed!'
        with open(log_file, encoding='utf-8') as f:
            assert logs[0] in f.read(), \
                f'No {logs[0]} have be found in {log_file}!'

    def test_register_a_file(self, log_file):
        # didn't test when log from other file
        register_logger(log_file, __file__)
        logger.info(logs[0])
        unregister_logger(log_file, __file__)
        assert os.path.isfile(log_file), f'Write {log_file} failed!'
        with open(log_file, encoding='utf-8') as f:
            assert logs[0] in f.read(), \
                f'No {logs[0]} have be found in {log_file}!'

    def test_register_a_module(self, log_file):
        # didn't test when log from other module
        register_logger(log_file, sys.modules['__main__'])
        logger.info(logs[0])
        unregister_logger(log_file, sys.modules['__main__'])
        assert os.path.isfile(log_file), f'Write {log_file} failed!'
        with open(log_file, encoding='utf-8') as f:
            assert logs[0] in f.read(), \
                f'No {logs[0]} have be found in {log_file}!'

    def test_register_a_class(self, log_file):
        register_logger(log_file, ClassA)
        ClassA(logs[0])
        ClassB(INVALID_LOG)
        unregister_logger(log_file, ClassA)
        assert os.path.isfile(log_file), f'Write {log_file} failed!'
        with open(log_file, encoding='utf-8') as f:
            log_content = f.read()
        assert logs[0] in log_content, \
            f'No {logs[0]} have be found in {log_file}!'
        assert INVALID_LOG not in log_content, \
            f'{INVALID_LOG} have be found in {log_file}!'

    def test_register_a_method(self, log_file):
        register_logger(log_file, ClassA.method_a)
        ClassA(INVALID_LOG).method_a(logs[0])
        unregister_logger(log_file, ClassA.method_a)
        assert os.path.isfile(log_file), f'Write {log_file} failed!'
        with open(log_file, encoding='utf-8') as f:
            log_content = f.read()
        assert logs[0] in log_content, \
            f'No {logs[0]} have be found in {log_file}!'
        assert INVALID_LOG not in log_content, \
            f'{INVALID_LOG} have be found in {log_file}!'

    def test_register_a_function(self, log_file):
        register_logger(log_file, function_a)
        function_a(logs[0])
        function_b(INVALID_LOG)
        unregister_logger(log_file, function_a)
        assert os.path.isfile(log_file), f'Write {log_file} failed!'
        with open(log_file, encoding='utf-8') as f:
            log_content = f.read()
        assert logs[0] in log_content, \
            f'No {logs[0]} have be found in {log_file}!'
        assert INVALID_LOG not in log_content, \
            f'{INVALID_LOG} have be found in {log_file}!'

    def test_register_multiple_objs(self, log_file):
        register_logger(log_file, function_a, function_b,
                        ClassA.method_a, ClassB.staticmethod_b)
        function_a(logs[0])
        function_b(logs[1])
        ClassA(INVALID_LOG).method_a(logs[2])
        ClassB(INVALID_LOG).staticmethod_b(logs[3])
        unregister_logger(log_file, function_a, ClassB.staticmethod_b)
        function_a(INVALID_LOG)
        function_b(logs[4])
        ClassA(INVALID_LOG).method_a(logs[5])
        ClassB(INVALID_LOG).staticmethod_b(INVALID_LOG)
        unregister_logger(log_file, function_b, ClassA.method_a)
        assert os.path.isfile(log_file), f'Write {log_file} failed!'
        with open(log_file, encoding='utf-8') as f:
            log_content = f.read()
        for log in logs:
            assert log in log_content, \
                f'No {log} have be found in {log_file}!'
        assert INVALID_LOG not in log_content, \
            f'{INVALID_LOG} have be found in {log_file}!'

    def test_register_to_a_exist_file(self, log_file):
        register_logger(log_file, function_a)
        register_logger(log_file, ClassA.method_a)
        function_a(logs[0])
        ClassA(INVALID_LOG).method_a(logs[1])
        unregister_logger(log_file)
        function_a(INVALID_LOG)
        ClassA(INVALID_LOG).method_a(INVALID_LOG)
        assert os.path.isfile(log_file), f'Write {log_file} failed!'
        with open(log_file, encoding='utf-8') as f:
            log_content = f.read()
        for log in logs[:2]:
            assert log in log_content, \
                f'No {log} have be found in {log_file}!'
        assert INVALID_LOG not in log_content, \
            f'{INVALID_LOG} have be found in {log_file}!'

    def test_register_to_different_file(self, log_file, another_log_file):
        register_logger(log_file, function_a)
        register_logger(another_log_file, ClassA.method_a)
        function_a(logs[0])
        ClassA(INVALID_LOG).method_a(logs[1])
        unregister_logger(log_file)
        function_a(INVALID_LOG)
        ClassA(INVALID_LOG).method_a(logs[2])
        unregister_logger(another_log_file)
        function_a(INVALID_LOG)
        ClassA(INVALID_LOG).method_a(INVALID_LOG)
        assert os.path.isfile(log_file), f'Write {log_file} failed!'
        assert os.path.isfile(another_log_file), \
            f'Write {another_log_file} failed!'

        with open(log_file, encoding='utf-8') as f:
            log_content = f.read()
        with open(another_log_file, encoding='utf-8') as f:
            another_log_content = f.read()

        assert logs[0] in log_content, \
            f'No {logs[0]} have be found in {log_file}!'
        for log in logs[1], logs[2], INVALID_LOG:
            assert log not in log_content, \
                f'{log} have be found in {log_file}!'

        for log in logs[1], logs[2]:
            assert log in another_log_content, \
                f'No {log} have be found in {log_file}!'
        for log in logs[0], INVALID_LOG:
            assert log not in another_log_content, \
                f'{log} have be found in {another_log_content}!'
