"""
实时检测API模块
Real-time detection API endpoints
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
import logging
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.service.DetectionService import get_detection_service, BEHAVIOR_CLASSES
from backend.model.ManagerModel import DatabaseManager
from backend.model.Detection_repositoryModel import DetectionRepository

logger = logging.getLogger(__name__)
detection_bp = Blueprint('detection', __name__)


def generate_alerts_for_detection(session_id: int, detections: list, behavior_summary: dict):
    """
    为检测结果生成预警
    
    Args:
        session_id: 会话ID
        detections: 检测结果列表
        behavior_summary: 行为统计
    """
    try:
        from backend.service.AlertService import get_alert_service
        from backend.service.Rule_engineService import EvaluationContext
        
        # 转换检测结果格式
        detection_dicts = []
        for det in detections:
            detection_dicts.append({
                'class_id': det.class_id,
                'class_name': det.class_name_cn,
                'confidence': det.confidence,
                'behavior_type': det.behavior_type,
                'bbox': det.bbox
            })
        
        # 创建评估上下文
        context = EvaluationContext(
            session_id=session_id,
            current_time=datetime.now(),
            behavior_counts=behavior_summary
        )
        
        # 生成预警
        alert_service = get_alert_service()
        alerts = alert_service.generate_alerts(detection_dicts, session_id, context)
        
        if alerts:
            logger.info(f"Generated {len(alerts)} alerts for session {session_id}")
        
        return alerts
    except Exception as e:
        logger.error(f"Failed to generate alerts: {e}")
        return []


@detection_bp.route('/detect', methods=['POST'])
@jwt_required()
def detect_image():
    """
    检测图片中的行为
    
    Request Body:
        {
            "image": "base64编码的图片",
            "confidence": 0.5,  # 可选，置信度阈值
            "iou": 0.45,  # 可选，IOU阈值
            "save_to_db": true  # 可选，是否保存到数据库
        }
    
    Response:
        {
            "success": true,
            "data": {
                "annotated_image": "base64编码的标注图片",
                "detections": [...],
                "total_count": 5,
                "warning_count": 2,
                "normal_count": 3,
                "behavior_summary": {...},
                "timestamp": "...",
                "session_id": 123  # 如果保存到数据库
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'message': '请提供图片数据'
            }), 400
        
        base64_image = data['image']
        confidence = data.get('confidence', 0.5)
        iou = data.get('iou', 0.45)
        save_to_db = data.get('save_to_db', True)  # 默认保存到数据库
        
        # 获取当前用户ID
        user_id = None
        try:
            claims = get_jwt()
            user_id = claims.get('user_id')
        except:
            pass
        
        # 获取检测服务
        service = get_detection_service()
        service.set_confidence_threshold(confidence)
        service.set_iou_threshold(iou)
        
        # 执行检测
        annotated_image, result = service.detect_base64(base64_image)
        
        response_data = {
            'annotated_image': annotated_image,
            **result.to_dict()
        }
        
        # 保存到数据库
        if save_to_db and result.detections:
            try:
                db = DatabaseManager()
                repo = DetectionRepository(db)
                
                # 创建检测会话
                session_id = repo.create_session(
                    source_type='image',
                    source_path=None,
                    user_id=user_id,
                    schedule_id=None
                )
                
                # 创建检测记录
                record_id = repo.create_record(
                    session_id=session_id,
                    frame_id=1,
                    timestamp=datetime.now().timestamp(),
                    alert_triggered=result.warning_count > 0,
                    detection_count=result.total_count
                )
                
                # 批量创建行为条目
                entries = []
                for det in result.detections:
                    entries.append({
                        'record_id': record_id,
                        'bbox': det.bbox,
                        'class_id': det.class_id,
                        'class_name': det.class_name_cn,
                        'confidence': det.confidence,
                        'behavior_type': det.behavior_type,
                        'alert_level': det.alert_level
                    })
                
                if entries:
                    repo.create_entries_batch(entries)
                
                # 更新会话状态
                repo.update_session(
                    session_id=session_id,
                    end_time=datetime.now(),
                    total_frames=1,
                    status='completed'
                )
                
                response_data['session_id'] = session_id
                logger.info(f"Detection saved to database: session_id={session_id}, detections={len(entries)}")
                
                # 生成预警
                if result.warning_count > 0:
                    alerts = generate_alerts_for_detection(
                        session_id, 
                        result.detections, 
                        result.behavior_summary
                    )
                    response_data['alerts_generated'] = len(alerts)
                
                db.close()
                
            except Exception as e:
                logger.error(f"Failed to save detection to database: {e}")
                # 不影响检测结果返回
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
        
    except ValueError as e:
        logger.error(f"Detection value error: {e}")
        return jsonify({
            'success': False,
            'message': f'图片数据无效: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify({
            'success': False,
            'message': f'检测失败: {str(e)}'
        }), 500


@detection_bp.route('/classes', methods=['GET'])
@jwt_required()
def get_behavior_classes():
    """获取行为类别列表"""
    try:
        classes = []
        for class_id, info in BEHAVIOR_CLASSES.items():
            classes.append({
                'class_id': class_id,
                'name': info['name'],
                'cn_name': info['cn_name'],
                'type': info['type'],
                'color': f"rgb({info['color'][0]},{info['color'][1]},{info['color'][2]})"
            })
        
        return jsonify({
            'success': True,
            'data': classes
        }), 200
    except Exception as e:
        logger.error(f"Get classes error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取类别失败: {str(e)}'
        }), 500


@detection_bp.route('/settings', methods=['GET'])
@jwt_required()
def get_detection_settings():
    """获取检测设置"""
    try:
        service = get_detection_service()
        return jsonify({
            'success': True,
            'data': {
                'confidence_threshold': service.confidence_threshold,
                'iou_threshold': service.iou_threshold,
                'model_loaded': service.model_loaded,
                'imgsz': service.imgsz,
                'use_half': service.use_half,
                'device': service.device
            }
        }), 200
    except Exception as e:
        logger.error(f"Get settings error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取设置失败: {str(e)}'
        }), 500


@detection_bp.route('/settings', methods=['POST'])
@jwt_required()
def update_detection_settings():
    """更新检测设置"""
    try:
        data = request.get_json()
        service = get_detection_service()
        
        if 'confidence_threshold' in data:
            service.set_confidence_threshold(data['confidence_threshold'])
        if 'iou_threshold' in data:
            service.set_iou_threshold(data['iou_threshold'])
        if 'imgsz' in data:
            service.set_imgsz(data['imgsz'])
        if 'use_half' in data:
            service.set_half_precision(data['use_half'])
        
        return jsonify({
            'success': True,
            'message': '设置已更新',
            'data': {
                'confidence_threshold': service.confidence_threshold,
                'iou_threshold': service.iou_threshold,
                'imgsz': service.imgsz,
                'use_half': service.use_half
            }
        }), 200
    except Exception as e:
        logger.error(f"Update settings error: {e}")
        return jsonify({
            'success': False,
            'message': f'更新设置失败: {str(e)}'
        }), 500



@detection_bp.route('/history', methods=['GET'])
@jwt_required()
def get_detection_history():
    """获取检测历史记录"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        db = DatabaseManager()
        repo = DetectionRepository(db)
        
        # 获取会话列表
        offset = (page - 1) * page_size
        sessions = repo.list_sessions(limit=page_size, offset=offset)
        total = repo.count_sessions()
        
        # 格式化返回数据
        history = []
        for session in sessions:
            # 获取该会话的行为统计
            entries = repo.get_entries_by_session(session['session_id'])
            behavior_counts = {}
            warning_count = 0
            for entry in entries:
                class_name = entry['class_name']
                behavior_counts[class_name] = behavior_counts.get(class_name, 0) + 1
                if entry['behavior_type'] == 'warning':
                    warning_count += 1
            
            history.append({
                'session_id': session['session_id'],
                'source_type': session['source_type'],
                'start_time': session['start_time'].isoformat() if session['start_time'] else None,
                'end_time': session['end_time'].isoformat() if session['end_time'] else None,
                'status': session['status'],
                'total_detections': len(entries),
                'warning_count': warning_count,
                'behavior_summary': behavior_counts
            })
        
        db.close()
        
        return jsonify({
            'success': True,
            'data': {
                'items': history,
                'total': total,
                'page': page,
                'page_size': page_size
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get history error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取历史记录失败: {str(e)}'
        }), 500


@detection_bp.route('/history/<int:session_id>', methods=['GET'])
@jwt_required()
def get_detection_detail(session_id):
    """获取单次检测详情"""
    try:
        db = DatabaseManager()
        repo = DetectionRepository(db)
        
        session = repo.get_session(session_id)
        if not session:
            db.close()
            return jsonify({
                'success': False,
                'message': '检测记录不存在'
            }), 404
        
        # 获取所有行为条目
        entries = repo.get_entries_by_session(session_id)
        
        # 格式化检测结果
        detections = []
        behavior_summary = {}
        warning_count = 0
        
        for entry in entries:
            detections.append({
                'class_id': entry['class_id'],
                'class_name': entry['class_name'],
                'confidence': float(entry['confidence']),
                'bbox': [entry['bbox_x1'], entry['bbox_y1'], entry['bbox_x2'], entry['bbox_y2']],
                'behavior_type': entry['behavior_type'],
                'alert_level': entry['alert_level']
            })
            
            class_name = entry['class_name']
            behavior_summary[class_name] = behavior_summary.get(class_name, 0) + 1
            if entry['behavior_type'] == 'warning':
                warning_count += 1
        
        db.close()
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session['session_id'],
                'source_type': session['source_type'],
                'start_time': session['start_time'].isoformat() if session['start_time'] else None,
                'end_time': session['end_time'].isoformat() if session['end_time'] else None,
                'status': session['status'],
                'detections': detections,
                'total_count': len(detections),
                'warning_count': warning_count,
                'normal_count': len(detections) - warning_count,
                'behavior_summary': behavior_summary
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get detection detail error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取检测详情失败: {str(e)}'
        }), 500


@detection_bp.route('/history/<int:session_id>', methods=['DELETE'])
@jwt_required()
def delete_detection(session_id):
    """删除检测记录"""
    try:
        db = DatabaseManager()
        repo = DetectionRepository(db)
        
        session = repo.get_session(session_id)
        if not session:
            db.close()
            return jsonify({
                'success': False,
                'message': '检测记录不存在'
            }), 404
        
        repo.delete_session(session_id)
        db.close()
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        }), 200
        
    except Exception as e:
        logger.error(f"Delete detection error: {e}")
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@detection_bp.route('/detect-fast', methods=['POST'])
@jwt_required()
def detect_image_fast():
    """
    快速检测图片（支持跳帧优化，用于实时检测）
    
    Request Body:
        {
            "image": "base64编码的图片",
            "confidence": 0.5,  # 可选，置信度阈值
            "skip_detection": false  # 可选，是否跳过检测使用缓存
        }
    
    Response:
        {
            "success": true,
            "data": {
                "annotated_image": "base64编码的标注图片",
                "detections": [...],
                "fps": 15.5,
                ...
            }
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'message': '请提供图片数据'
            }), 400
        
        base64_image = data['image']
        confidence = data.get('confidence', 0.45)
        skip_detection = data.get('skip_detection', False)
        
        # 获取检测服务
        service = get_detection_service()
        service.set_confidence_threshold(confidence)
        
        # 执行快速检测
        annotated_image, result = service.detect_base64_fast(base64_image, skip_detection)
        
        response_data = {
            'annotated_image': annotated_image,
            'fps': service.get_fps(),
            **result.to_dict()
        }
        
        return jsonify({
            'success': True,
            'data': response_data
        }), 200
        
    except ValueError as e:
        logger.error(f"Fast detection value error: {e}")
        return jsonify({
            'success': False,
            'message': f'图片数据无效: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Fast detection error: {e}")
        return jsonify({
            'success': False,
            'message': f'检测失败: {str(e)}'
        }), 500


@detection_bp.route('/frame-skip', methods=['GET'])
@jwt_required()
def get_frame_skip():
    """获取跳帧设置"""
    try:
        service = get_detection_service()
        return jsonify({
            'success': True,
            'data': {
                'frame_skip': service._frame_skip,
                'fps': service.get_fps()
            }
        }), 200
    except Exception as e:
        logger.error(f"Get frame skip error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取跳帧设置失败: {str(e)}'
        }), 500


@detection_bp.route('/frame-skip', methods=['POST'])
@jwt_required()
def set_frame_skip():
    """设置跳帧数"""
    try:
        data = request.get_json()
        frame_skip = data.get('frame_skip', 2)
        
        service = get_detection_service()
        service.set_frame_skip(frame_skip)
        
        return jsonify({
            'success': True,
            'message': '跳帧设置已更新',
            'data': {
                'frame_skip': service._frame_skip
            }
        }), 200
    except Exception as e:
        logger.error(f"Set frame skip error: {e}")
        return jsonify({
            'success': False,
            'message': f'设置跳帧失败: {str(e)}'
        }), 500


@detection_bp.route('/time-statistics', methods=['GET'])
@jwt_required()
def get_time_statistics():
    """获取行为时间统计"""
    try:
        service = get_detection_service()
        stats = service.get_time_statistics()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
    except Exception as e:
        logger.error(f"Get time statistics error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取时间统计失败: {str(e)}'
        }), 500


@detection_bp.route('/time-statistics/reset', methods=['POST'])
@jwt_required()
def reset_time_statistics():
    """重置行为时间统计"""
    try:
        service = get_detection_service()
        service.reset_time_tracker()
        
        return jsonify({
            'success': True,
            'message': '时间统计已重置'
        }), 200
    except Exception as e:
        logger.error(f"Reset time statistics error: {e}")
        return jsonify({
            'success': False,
            'message': f'重置时间统计失败: {str(e)}'
        }), 500


# 标准视频检测接口已移除 - 已被 detect-video-optimized 替代
# 原接口 /detect-video 前端未使用，移除以提高性能


@detection_bp.route('/detect-video-optimized', methods=['POST'])
@jwt_required()
def detect_video_optimized():
    """
    优化的视频检测（GPU 批处理加速）
    
    Request:
        multipart/form-data with 'video' file
        Optional parameters:
        - confidence: float (default 0.45)
        - frame_skip: int (default 3, 更积极的跳帧)
        - batch_size: int (default 8, GPU 批处理大小)
        
    Response:
        {
            "success": true,
            "data": {
                "session_id": 123,
                "total_frames": 100,
                "processed_frames": 25,
                "processing_time": 15.2,
                "avg_fps": 1.6,
                "detections_summary": {...}
            }
        }
    """
    try:
        if 'video' not in request.files:
            return jsonify({
                'success': False,
                'message': '请上传视频文件'
            }), 400
        
        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({
                'success': False,
                'message': '请选择视频文件'
            }), 400
        
        # 获取参数
        confidence = float(request.form.get('confidence', 0.45))
        frame_skip = int(request.form.get('frame_skip', 3))  # 更积极的跳帧
        batch_size = int(request.form.get('batch_size', 8))  # GPU 批处理大小
        
        # 保存临时文件
        import tempfile
        import os as temp_os
        import time
        
        temp_dir = tempfile.gettempdir()
        temp_path = temp_os.path.join(temp_dir, f"video_opt_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp4")
        video_file.save(temp_path)
        
        try:
            # 获取检测服务
            service = get_detection_service()
            service.set_confidence_threshold(confidence)
            
            # 创建数据库会话
            db = DatabaseManager()
            repo = DetectionRepository(db)
            
            user_id = None
            try:
                claims = get_jwt()
                user_id = claims.get('user_id')
            except:
                pass
            
            session_id = repo.create_session(
                source_type='video_optimized',
                source_path=video_file.filename,
                user_id=user_id,
                schedule_id=None
            )
            
            # 开始计时
            start_time = time.time()
            
            # 使用优化的视频检测
            import cv2
            cap = cv2.VideoCapture(temp_path)
            
            if not cap.isOpened():
                return jsonify({
                    'success': False,
                    'message': '无法打开视频文件'
                }), 400
            
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"开始优化视频处理: {total_frames} 帧, 批大小: {batch_size}, 跳帧: {frame_skip}")
            
            # 收集需要处理的帧
            frames_batch = []
            frame_indices = []
            frame_count = 0
            processed_count = 0
            all_detections = []
            behavior_totals = {}
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                
                # 跳帧处理
                if frame_count % (frame_skip + 1) != 0:
                    continue
                
                frames_batch.append(frame.copy())
                frame_indices.append(frame_count)
                
                # 当收集到足够的帧时，进行批处理
                if len(frames_batch) >= batch_size:
                    # 批量检测
                    batch_results = service.detect_batch(frames_batch, batch_size)
                    
                    # 处理批次结果
                    for i, result in enumerate(batch_results):
                        if result.detections:
                            frame_idx = frame_indices[i]
                            record_id = repo.create_record(
                                session_id=session_id,
                                frame_id=frame_idx,
                                timestamp=frame_idx / fps if fps > 0 else 0,
                                alert_triggered=result.warning_count > 0,
                                detection_count=result.total_count
                            )
                            
                            entries = []
                            for det in result.detections:
                                entries.append({
                                    'record_id': record_id,
                                    'bbox': det.bbox,
                                    'class_id': det.class_id,
                                    'class_name': det.class_name_cn,
                                    'confidence': det.confidence,
                                    'behavior_type': det.behavior_type,
                                    'alert_level': det.alert_level
                                })
                                
                                # 统计行为
                                behavior_totals[det.class_name_cn] = behavior_totals.get(det.class_name_cn, 0) + 1
                            
                            if entries:
                                repo.create_entries_batch(entries)
                            
                            all_detections.extend(result.detections)
                    
                    processed_count += len(frames_batch)
                    
                    # 清空批次
                    frames_batch = []
                    frame_indices = []
                    
                    # 记录进度
                    progress = processed_count / (total_frames // (frame_skip + 1))
                    logger.info(f"处理进度: {progress:.1%} ({processed_count} 帧)")
            
            # 处理剩余的帧
            if frames_batch:
                batch_results = service.detect_batch(frames_batch, len(frames_batch))
                
                for i, result in enumerate(batch_results):
                    if result.detections:
                        frame_idx = frame_indices[i]
                        record_id = repo.create_record(
                            session_id=session_id,
                            frame_id=frame_idx,
                            timestamp=frame_idx / fps if fps > 0 else 0,
                            alert_triggered=result.warning_count > 0,
                            detection_count=result.total_count
                        )
                        
                        entries = []
                        for det in result.detections:
                            entries.append({
                                'record_id': record_id,
                                'bbox': det.bbox,
                                'class_id': det.class_id,
                                'class_name': det.class_name_cn,
                                'confidence': det.confidence,
                                'behavior_type': det.behavior_type,
                                'alert_level': det.alert_level
                            })
                            
                            behavior_totals[det.class_name_cn] = behavior_totals.get(det.class_name_cn, 0) + 1
                        
                        if entries:
                            repo.create_entries_batch(entries)
                        
                        all_detections.extend(result.detections)
                
                processed_count += len(frames_batch)
            
            cap.release()
            
            # 计算处理时间
            processing_time = time.time() - start_time
            avg_fps = processed_count / processing_time if processing_time > 0 else 0
            
            # 更新会话
            repo.update_session(
                session_id=session_id,
                end_time=datetime.now(),
                total_frames=processed_count,
                status='completed'
            )
            
            db.close()
            
            # 统计结果
            total_detections = len(all_detections)
            warning_count = sum(1 for d in all_detections if d.behavior_type == 'warning')
            
            logger.info(f"优化视频处理完成: {processing_time:.2f}s, 平均 {avg_fps:.1f} FPS")
            
            return jsonify({
                'success': True,
                'data': {
                    'session_id': session_id,
                    'total_frames': total_frames,
                    'processed_frames': processed_count,
                    'video_fps': fps,
                    'processing_time': round(processing_time, 2),
                    'avg_fps': round(avg_fps, 1),
                    'frame_skip': frame_skip,
                    'batch_size': batch_size,
                    'total_detections': total_detections,
                    'warning_count': warning_count,
                    'normal_count': total_detections - warning_count,
                    'behavior_summary': behavior_totals,
                    'optimization': {
                        'gpu_accelerated': service.device != 'cpu',
                        'batch_processing': True,
                        'half_precision': service.use_half,
                        'image_size': service.imgsz
                    }
                }
            }), 200
            
        finally:
            # 清理临时文件
            if temp_os.path.exists(temp_path):
                temp_os.remove(temp_path)
        
    except Exception as e:
        logger.error(f"Optimized video detection error: {e}")
        return jsonify({
            'success': False,
            'message': f'优化视频检测失败: {str(e)}'
        }), 500


@detection_bp.route('/gpu-info', methods=['GET'])
@jwt_required()
def get_gpu_info():
    """获取 GPU 信息和使用情况"""
    try:
        service = get_detection_service()
        model_info = service.get_model_info()
        
        return jsonify({
            'success': True,
            'data': model_info
        }), 200
    except Exception as e:
        logger.error(f"Get GPU info error: {e}")
        return jsonify({
            'success': False,
            'message': f'获取 GPU 信息失败: {str(e)}'
        }), 500


# ==================== PySide6 桌面应用集成 API ====================

@detection_bp.route('/session/start', methods=['POST'])
@jwt_required()
def start_detection_session():
    """
    创建检测会话（供 PySide6 桌面应用调用）
    
    Request Body:
        {
            "class_id": 1,  # 可选，班级ID
            "source_type": "pyside6_realtime"  # 来源类型
        }
    
    Response:
        {
            "success": true,
            "data": {
                "session_id": 123
            }
        }
    """
    try:
        data = request.get_json() or {}
        class_id = data.get('class_id')
        source_type = data.get('source_type', 'pyside6_realtime')
        
        # 获取当前用户ID
        user_id = None
        try:
            claims = get_jwt()
            user_id = claims.get('user_id')
        except:
            pass
        
        db = DatabaseManager()
        repo = DetectionRepository(db)
        
        session_id = repo.create_session(
            source_type=source_type,
            source_path=None,
            user_id=user_id,
            schedule_id=None
        )
        
        db.close()
        
        logger.info(f"Created detection session: {session_id} for user {user_id}")
        
        return jsonify({
            'success': True,
            'data': {
                'session_id': session_id
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Start session error: {e}")
        return jsonify({
            'success': False,
            'message': f'创建会话失败: {str(e)}'
        }), 500


@detection_bp.route('/session/end', methods=['POST'])
@jwt_required()
def end_detection_session():
    """
    结束检测会话
    
    Request Body:
        {
            "session_id": 123
        }
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({
                'success': False,
                'message': '请提供会话ID'
            }), 400
        
        db = DatabaseManager()
        repo = DetectionRepository(db)
        
        repo.update_session(
            session_id=session_id,
            end_time=datetime.now(),
            status='completed'
        )
        
        db.close()
        
        logger.info(f"Ended detection session: {session_id}")
        
        return jsonify({
            'success': True,
            'message': '会话已结束'
        }), 200
        
    except Exception as e:
        logger.error(f"End session error: {e}")
        return jsonify({
            'success': False,
            'message': f'结束会话失败: {str(e)}'
        }), 500


@detection_bp.route('/save', methods=['POST'])
@jwt_required()
def save_detection_result():
    """
    保存检测结果（供 PySide6 桌面应用调用）
    
    Request Body:
        {
            "session_id": 123,
            "detections": [...],
            "total_count": 5,
            "warning_count": 2,
            "normal_count": 3,
            "behavior_summary": {...},
            "timestamp": "..."
        }
    """
    try:
        data = request.get_json()
        
        session_id = data.get('session_id')
        detections = data.get('detections', [])
        
        if not session_id:
            return jsonify({
                'success': False,
                'message': '请提供会话ID'
            }), 400
        
        if not detections:
            return jsonify({
                'success': True,
                'message': '无检测结果需要保存'
            }), 200
        
        db = DatabaseManager()
        repo = DetectionRepository(db)
        
        # 创建检测记录
        record_id = repo.create_record(
            session_id=session_id,
            frame_id=data.get('frame_id', 0),
            timestamp=datetime.now().timestamp(),
            alert_triggered=data.get('warning_count', 0) > 0,
            detection_count=data.get('total_count', len(detections))
        )
        
        # 批量创建行为条目
        entries = []
        for det in detections:
            entries.append({
                'record_id': record_id,
                'bbox': det.get('bbox', [0, 0, 0, 0]),
                'class_id': det.get('class_id', 0),
                'class_name': det.get('class_name_cn', det.get('class_name', '')),
                'confidence': det.get('confidence', 0),
                'behavior_type': det.get('behavior_type', 'normal'),
                'alert_level': det.get('alert_level', 0)
            })
        
        if entries:
            repo.create_entries_batch(entries)
        
        # 更新会话统计
        repo.update_session(
            session_id=session_id,
            total_frames=repo.count_records_by_session(session_id)
        )
        
        db.close()
        
        # 生成预警（如果有预警行为）
        if data.get('warning_count', 0) > 0:
            try:
                # 转换检测结果格式
                detection_dicts = []
                for det in detections:
                    detection_dicts.append({
                        'class_id': det.get('class_id', 0),
                        'class_name': det.get('class_name_cn', det.get('class_name', '')),
                        'confidence': det.get('confidence', 0),
                        'behavior_type': det.get('behavior_type', 'normal'),
                        'bbox': det.get('bbox', [0, 0, 0, 0])
                    })
                
                from backend.service.AlertService import get_alert_service
                from backend.service.Rule_engineService import EvaluationContext
                
                context = EvaluationContext(
                    session_id=session_id,
                    current_time=datetime.now(),
                    behavior_counts=data.get('behavior_summary', {})
                )
                
                alert_service = get_alert_service()
                alerts = alert_service.generate_alerts(detection_dicts, session_id, context)
                
                logger.info(f"Generated {len(alerts)} alerts for session {session_id}")
            except Exception as e:
                logger.error(f"Failed to generate alerts: {e}")
        
        return jsonify({
            'success': True,
            'data': {
                'record_id': record_id,
                'entries_saved': len(entries)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Save detection error: {e}")
        return jsonify({
            'success': False,
            'message': f'保存检测结果失败: {str(e)}'
        }), 500


@detection_bp.route('/launch-desktop', methods=['POST'])
@jwt_required()
def launch_desktop_app():
    """
    启动 PySide6 桌面检测应用
    
    Response:
        {
            "success": true,
            "message": "桌面应用已启动"
        }
    """
    try:
        import subprocess
        import os as launch_os
        
        # 获取桌面应用路径
        project_root = launch_os.path.dirname(launch_os.path.dirname(launch_os.path.dirname(launch_os.path.abspath(__file__))))
        app_path = launch_os.path.join(project_root, 'backend', 'presentation', 'gui', 'pyside6_app.py')
        
        if not launch_os.path.exists(app_path):
            return jsonify({
                'success': False,
                'message': '桌面应用文件不存在'
            }), 404
        
        # 启动桌面应用（非阻塞）
        subprocess.Popen(
            ['python', app_path],
            cwd=project_root,
            creationflags=subprocess.CREATE_NEW_CONSOLE if launch_os.name == 'nt' else 0
        )
        
        logger.info("Launched PySide6 desktop detection app")
        
        return jsonify({
            'success': True,
            'message': '桌面应用已启动'
        }), 200
        
    except Exception as e:
        logger.error(f"Launch desktop app error: {e}")
        return jsonify({
            'success': False,
            'message': f'启动桌面应用失败: {str(e)}'
        }), 500
