# cache
from __future__ import annotations

import os
from functools import cached_property
from pathlib import Path
from typing import TypeVar

from infinity_emb.primitives import (
    Device,
    Dtype,
    EmbeddingDtype,
    EnumType,
    InferenceEngine,
    PoolingMethod,
)

EnumTypeLike = TypeVar("EnumTypeLike", bound=EnumType)


class __Infinity_EnvManager:
    def __init__(self):
        self._debug(f"Loading Infinity ENV variables.\nCONFIG:\n{'-'*10}")
        for f_name in dir(self):
            if isinstance(getattr(type(self), f_name, None), cached_property):
                getattr(self, f_name)  # pre-cache
        self._debug(f"{'-'*10}\nENV variables loaded.")

    def _debug(self, message: str):
        """print as debug without having to import logging."""
        if "LOG_LEVEL" in message:
            return  # recursion
        elif self.log_level in {"debug", "trace"}:
            if "API_KEY" in message:
                print("INFINITY_API_KEY=not_shown")
                print(f"INFINITY_LOG_LEVEL={self.log_level}")
            else:
                print(message)

    @staticmethod
    def _to_name(name: str) -> str:
        return "INFINITY_" + name.upper().replace("-", "_")

    def _optional_infinity_var(self, name: str, default: str = ""):
        name = self._to_name(name)
        value = os.getenv(name)
        if value is None:
            self._debug(f"{name}=`{default}`(default)")
            return default
        self._debug(f"{name}=`{value}`")
        return value

    def _optional_infinity_var_multiple(
        self, name: str, default: list[str]
    ) -> list[str]:
        name = self._to_name(name)
        value = os.getenv(name)
        if value is None:
            self._debug(f"{name}=`{';'.join(default)}`(default)")
            return default
        if value.endswith(";"):
            value = value[:-1]
        value_list = value.split(";")
        self._debug(f"{name}=`{';'.join(value_list)}`")
        return value_list

    @staticmethod
    def _to_bool(value: str) -> bool:
        return value.lower() in {"true", "1"}

    @staticmethod
    def _to_bool_multiple(value: list[str]) -> list[bool]:
        return [v.lower() in {"true", "1"} for v in value]

    @staticmethod
    def _to_int_multiple(value: list[str]) -> list[int]:
        return [int(v) for v in value]

    @cached_property
    def api_key(self):
        return self._optional_infinity_var("api_key", default="")

    @cached_property
    def model_id(self):
        return self._optional_infinity_var_multiple(
            "model_id", default=["michaelfeil/bge-small-en-v1.5"]
        )

    @cached_property
    def served_model_name(self):
        return self._optional_infinity_var_multiple("served_model_name", default=[""])

    @cached_property
    def batch_size(self):
        return self._to_int_multiple(
            self._optional_infinity_var_multiple("batch_size", default=["32"])
        )

    @cached_property
    def revision(self):
        return self._optional_infinity_var_multiple("revision", default=[""])

    @cached_property
    def trust_remote_code(self):
        return self._to_bool_multiple(
            self._optional_infinity_var_multiple("trust_remote_code", default=["true"])
        )

    @cached_property
    def model_warmup(self):
        return self._to_bool_multiple(
            self._optional_infinity_var_multiple("model_warmup", default=["true"])
        )

    @cached_property
    def vector_disk_cache(self):
        return self._to_bool_multiple(
            self._optional_infinity_var_multiple("vector_disk_cache", default=["false"])
        )

    @cached_property
    def lengths_via_tokenize(self):
        return self._to_bool_multiple(
            self._optional_infinity_var_multiple(
                "lengths_via_tokenize", default=["false"]
            )
        )

    @cached_property
    def compile(self):
        return self._to_bool_multiple(
            self._optional_infinity_var_multiple("compile", default=["false"])
        )

    @cached_property
    def bettertransformer(self):
        return self._to_bool_multiple(
            self._optional_infinity_var_multiple("bettertransformer", default=["true"])
        )

    @cached_property
    def preload_only(self):
        return self._to_bool(
            self._optional_infinity_var("preload_only", default="false")
        )

    @cached_property
    def calibration_dataset_url(self):
        return self._optional_infinity_var(
            "calibration_dataset_url",
            default="https://raw.githubusercontent.com/michaelfeil/infinity/2da1f32d610b8edbe4ce58d0c44fc27c963abca6/docs/assets/multilingual_calibration.utf8",
        )

    @cached_property
    def infinity_cache_dir(self) -> Path:
        """gets the cache directory for infinity_emb."""
        cache_dir = None
        hf_home = os.environ.get("HF_HOME")
        inf_home = os.environ.get("INFINITY_HOME")
        if inf_home:
            cache_dir = Path(inf_home) / ".infinity_cache"
        elif hf_home:
            cache_dir = Path(hf_home) / ".infinity_cache"
        else:
            cache_dir = Path(".").resolve() / ".infinity_cache"

        if not cache_dir.exists():
            cache_dir.mkdir(parents=True, exist_ok=True)

        return cache_dir

    @cached_property
    def permissive_cors(self):
        return self._to_bool(
            self._optional_infinity_var("permissive_cors", default="false")
        )

    @cached_property
    def url_prefix(self):
        return self._optional_infinity_var("url_prefix", default="")

    @cached_property
    def port(self):
        port = self._optional_infinity_var("port", default="7997")
        assert port.isdigit(), "INFINITY_PORT must be a number"
        return int(port)

    @cached_property
    def host(self):
        return self._optional_infinity_var("host", default="0.0.0.0")

    @cached_property
    def redirect_slash(self):
        route = self._optional_infinity_var("redirect_slash", default="/docs")
        assert not route or route.startswith(
            "/"
        ), "INFINITY_REDIRECT_SLASH must start with /"
        return route

    @cached_property
    def log_level(self):
        return self._optional_infinity_var("log_level", default="info")

    def _typed_multiple(self, name: str, cls: type["EnumTypeLike"]) -> list["str"]:
        result = self._optional_infinity_var_multiple(
            name, default=[cls.default_value()]
        )
        assert all(cls(v) for v in result)
        return result

    @cached_property
    def dtype(self) -> list[str]:
        return self._typed_multiple("dtype", cls=Dtype)

    @cached_property
    def engine(self) -> list[str]:
        return self._typed_multiple("engine", InferenceEngine)

    @cached_property
    def pooling_method(self) -> list[str]:
        return self._typed_multiple("pooling_method", PoolingMethod)

    @cached_property
    def device(self) -> list[str]:
        return self._typed_multiple("device", Device)

    @cached_property
    def embedding_dtype(self) -> list[str]:
        return self._typed_multiple("embedding_dtype", EmbeddingDtype)


MANAGER = __Infinity_EnvManager()
