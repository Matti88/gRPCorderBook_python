# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: data_stream.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'data_stream.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11\x64\x61ta_stream.proto\x12\ndatastream\"\x07\n\x05\x45mpty\":\n\tDataPoint\x12\x14\n\x0cnormal_value\x18\x01 \x01(\x01\x12\x17\n\x0fpower_law_value\x18\x02 \x01(\x01\x32H\n\x0c\x44\x61taStreamer\x12\x38\n\nStreamData\x12\x11.datastream.Empty\x1a\x15.datastream.DataPoint0\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data_stream_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_EMPTY']._serialized_start=33
  _globals['_EMPTY']._serialized_end=40
  _globals['_DATAPOINT']._serialized_start=42
  _globals['_DATAPOINT']._serialized_end=100
  _globals['_DATASTREAMER']._serialized_start=102
  _globals['_DATASTREAMER']._serialized_end=174
# @@protoc_insertion_point(module_scope)
