"""
Agent API 路由
提供 WebSocket 和 HTTP 接口用于智能书单生成
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
import asyncio
import logging

from ..agents.workflow import workflow_manager, BookListWorkflow

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v2/agent", tags=["Agent"])


class AgentChatRequest(BaseModel):
    """Agent 对话请求"""
    message: str
    session_id: Optional[str] = None


class AgentChatResponse(BaseModel):
    """Agent 对话响应"""
    success: bool
    data: Dict[str, Any]
    session_id: str


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest):
    """
    Agent 对话接口（非流式）
    
    完整的同步书单生成接口
    """
    try:
        # 获取或创建工作流
        if request.session_id:
            workflow = workflow_manager.get_workflow(request.session_id)
            if not workflow:
                workflow = workflow_manager.create_workflow(request.session_id)
        else:
            workflow = workflow_manager.create_workflow()
        
        # 执行工作流
        result = await workflow.execute_sync(request.message)
        
        return AgentChatResponse(
            success=result["type"] == "complete",
            data=result,
            session_id=workflow.session_id
        )
        
    except Exception as e:
        logger.error(f"Agent chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def agent_chat_stream(request: AgentChatRequest):
    """
    Agent 对话接口（流式）
    
    使用 Server-Sent Events 返回实时进度
    """
    async def event_generator():
        try:
            # 获取或创建工作流
            if request.session_id:
                workflow = workflow_manager.get_workflow(request.session_id)
                if not workflow:
                    workflow = workflow_manager.create_workflow(request.session_id)
            else:
                workflow = workflow_manager.create_workflow()
            
            # 执行工作流并流式输出
            async for msg in workflow.execute(request.message, stream=True):
                yield f"data: {json.dumps(msg)}\n\n"
                
        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.websocket("/ws")
async def agent_websocket(websocket: WebSocket):
    """
    WebSocket 实时对话接口
    
    支持双向通信，实时展示思考过程
    """
    # 接受 WebSocket 连接
    await websocket.accept()
    workflow = None
    
    # 获取认证 token（从查询参数）
    token = websocket.query_params.get("token")
    if token:
        # 验证 token（如果需要）
        from app.services.auth_service import AuthService
        user = AuthService.get_current_user(token)
        if user:
            logger.info(f"WebSocket connected with user: {user.username}")
        else:
            logger.warning("WebSocket connected with invalid token")
    
    try:
        while True:
            # 接收用户消息
            data = await websocket.receive_json()
            action = data.get("action", "chat")
            
            if action == "chat":
                message = data.get("message", "")
                session_id = data.get("session_id")
                
                # 获取或创建工作流
                if session_id:
                    workflow = workflow_manager.get_workflow(session_id)
                    if not workflow:
                        workflow = workflow_manager.create_workflow(session_id)
                else:
                    workflow = workflow_manager.create_workflow()
                    # 发送会话ID
                    await websocket.send_json({
                        "type": "session_created",
                        "session_id": workflow.session_id
                    })
                
                # 执行工作流
                async for msg in workflow.execute(message, stream=True):
                    await websocket.send_json(msg)
                    
                    # 添加小延迟，避免消息过快
                    await asyncio.sleep(0.1)
            
            elif action == "history":
                # 获取会话历史
                session_id = data.get("session_id")
                if session_id:
                    workflow = workflow_manager.get_workflow(session_id)
                    if workflow:
                        await websocket.send_json({
                            "type": "history",
                            "history": workflow.history
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "content": "会话不存在"
                        })
            
            elif action == "clear":
                # 清除会话
                session_id = data.get("session_id")
                if session_id:
                    workflow_manager.remove_workflow(session_id)
                    await websocket.send_json({
                        "type": "cleared",
                        "content": "会话已清除"
                    })
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {workflow.session_id if workflow else 'unknown'}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "content": str(e)
            })
        except:
            pass


@router.get("/health")
async def agent_health():
    """Agent 服务健康检查"""
    return {
        "status": "healthy",
        "active_sessions": len(workflow_manager.workflows),
        "service": "agent_workflow"
    }


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    workflow_manager.remove_workflow(session_id)
    return {"success": True, "message": "会话已删除"}
