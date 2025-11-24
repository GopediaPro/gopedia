import grpc
import logging
from google.protobuf.json_format import ParseDict, MessageToDict

# Generated code imports
# (경로 문제 해결을 위해 try-except 혹은 상대 경로 조정 필요. 여기선 절대 경로 가정)
from core.plugin.generated import gopedia_pb2, gopedia_pb2_grpc
from core.plugin.interface import PluginClientInterface
from domain.schemas.plugin import PluginPayload, PluginResult

logger = logging.getLogger(__name__)

class GrpcPluginClient(PluginClientInterface):
    """
    실제 gRPC 통신을 담당하는 구현체.
    Pydantic Model <-> Protobuf Struct 변환을 수행합니다.
    """

    def __init__(self):
        self.channel = None
        self.stub = None

    async def connect(self, service_address: str) -> None:
        """비동기 채널 생성"""
        self.channel = grpc.aio.insecure_channel(service_address)
        self.stub = gopedia_pb2_grpc.PluginServiceStub(self.channel)
        logger.info(f"🔌 Connected to Plugin Service at {service_address}")

    async def execute(self, payload: PluginPayload) -> PluginResult:
        if not self.stub:
            raise ConnectionError("Plugin client is not connected.")

        # 1. Pydantic -> Protobuf Request 변환
        req = gopedia_pb2.PluginRequest(
            context_urn=payload.context_urn or "",
            operation=payload.operation
        )
        
        # JSON(Dict)을 Protobuf Struct로 변환
        if payload.params:
            ParseDict(payload.params, req.params)
        if payload.data_snapshot:
            ParseDict(payload.data_snapshot, req.payload)

        try:
            # 2. gRPC Call (Async)
            response = await self.stub.Execute(req)

            # 3. Protobuf Response -> Pydantic 변환
            result_data = MessageToDict(response.data) if response.data else None
            
            return PluginResult(
                success=response.success,
                error_message=response.error_message,
                data=result_data
            )

        except grpc.RpcError as e:
            logger.error(f"gRPC Error: {e.code()} - {e.details()}")
            return PluginResult(success=False, error_message=f"RPC Error: {e.details()}")

    async def close(self):
        if self.channel:
            await self.channel.close()