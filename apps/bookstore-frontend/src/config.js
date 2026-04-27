/**
 * 前端配置文件
 *
 * 管理应用的配置信息，包括API地址、轮询间隔和上传限制等
 *
 * @author System
 * @date 2026-01-31
 */

import { getApiBaseUrl } from './utils/apiBase'

// API基础URL - 统一从同一个基线读取
export const API_BASE_URL = getApiBaseUrl()

// 轮询配置
export const POLLING_INTERVAL = 3000; // 3秒

// 上传配置
export const MAX_UPLOAD_SIZE = 10 * 1024 * 1024; // 10MB
