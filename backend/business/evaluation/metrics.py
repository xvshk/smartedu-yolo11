"""
指标计算模块
Metrics calculation model for model evaluation.
"""
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import numpy as np

from .models import (
    Detection,
    ClassMetrics,
    OverallMetrics,
    GroupMetrics,
    ConfusedPair,
)


class MetricsCalculator:
    """
    评估指标计算器
    Calculator for evaluation metrics including mAP, precision, recall, F1, and confusion matrix.
    """
    
    # 正常行为类别 ID
    NORMAL_CLASSES = [0, 1, 2]  # handrise, read, write
    
    # 预警行为类别 ID
    WARNING_CLASSES = [3, 4, 5, 6]  # sleep, stand, using_electronic_devices, talk
    
    def __init__(self, num_classes: int = 7):
        """
        初始化计算器
        
        Args:
            num_classes: 类别数量，默认为 7
        """
        self.num_classes = num_classes
        self.class_names = [
            'handrise', 'read', 'write', 'sleep',
            'stand', 'using_electronic_devices', 'talk'
        ]
        self.class_names_cn = [
            '举手', '阅读', '书写', '睡觉',
            '站立', '使用电子设备', '交谈'
        ]
    
    def _compute_iou(self, box1: List[float], box2: List[float]) -> float:
        """
        计算两个边界框的 IoU
        
        Args:
            box1: [x1, y1, x2, y2]
            box2: [x1, y1, x2, y2]
            
        Returns:
            IoU 值
        """
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        inter_area = max(0, x2 - x1) * max(0, y2 - y1)
        
        box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
        box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        union_area = box1_area + box2_area - inter_area
        
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
    
    def _match_predictions(
        self,
        predictions: List[Detection],
        ground_truths: List[Detection],
        iou_threshold: float = 0.5
    ) -> Tuple[List[bool], List[bool]]:
        """
        匹配预测和真实标签
        
        Args:
            predictions: 预测结果列表
            ground_truths: 真实标签列表
            iou_threshold: IoU 阈值
            
        Returns:
            (pred_matched, gt_matched) 两个布尔列表
        """
        pred_matched = [False] * len(predictions)
        gt_matched = [False] * len(ground_truths)
        
        # 按图像分组
        preds_by_image = defaultdict(list)
        gts_by_image = defaultdict(list)
        
        for i, pred in enumerate(predictions):
            preds_by_image[pred.image_id].append((i, pred))
        
        for i, gt in enumerate(ground_truths):
            gts_by_image[gt.image_id].append((i, gt))
        
        # 对每张图像进行匹配
        for image_id in set(preds_by_image.keys()) | set(gts_by_image.keys()):
            img_preds = preds_by_image.get(image_id, [])
            img_gts = gts_by_image.get(image_id, [])
            
            # 按置信度排序预测
            img_preds.sort(key=lambda x: x[1].confidence, reverse=True)
            
            for pred_idx, pred in img_preds:
                best_iou = 0
                best_gt_idx = -1
                
                for gt_idx, gt in img_gts:
                    if gt_matched[gt_idx]:
                        continue
                    if pred.class_id != gt.class_id:
                        continue
                    
                    iou = self._compute_iou(pred.bbox, gt.bbox)
                    if iou > best_iou and iou >= iou_threshold:
                        best_iou = iou
                        best_gt_idx = gt_idx
                
                if best_gt_idx >= 0:
                    pred_matched[pred_idx] = True
                    gt_matched[best_gt_idx] = True
        
        return pred_matched, gt_matched
    
    def _compute_ap(
        self,
        precisions: List[float],
        recalls: List[float]
    ) -> float:
        """
        计算 Average Precision (AP)
        
        Args:
            precisions: 精确率列表
            recalls: 召回率列表
            
        Returns:
            AP 值
        """
        if not precisions or not recalls:
            return 0.0
        
        # 添加起始点和结束点
        precisions = [0.0] + list(precisions) + [0.0]
        recalls = [0.0] + list(recalls) + [1.0]
        
        # 使精确率单调递减
        for i in range(len(precisions) - 2, -1, -1):
            precisions[i] = max(precisions[i], precisions[i + 1])
        
        # 计算 AP
        ap = 0.0
        for i in range(1, len(recalls)):
            if recalls[i] != recalls[i - 1]:
                ap += (recalls[i] - recalls[i - 1]) * precisions[i]
        
        return ap
    
    def compute_overall_metrics(
        self,
        predictions: List[Detection],
        ground_truths: List[Detection],
        iou_threshold: float = 0.5
    ) -> OverallMetrics:
        """
        计算整体指标
        
        Args:
            predictions: 预测结果列表
            ground_truths: 真实标签列表
            iou_threshold: IoU 阈值
            
        Returns:
            OverallMetrics 包含 mAP50, mAP50-95, precision, recall, F1
        """
        if not predictions and not ground_truths:
            return OverallMetrics(
                mAP50=0.0, mAP50_95=0.0, precision=0.0, recall=0.0, f1_score=0.0,
                total_images=0, total_predictions=0, total_ground_truths=0
            )
        
        # 获取唯一图像数
        image_ids = set()
        for p in predictions:
            image_ids.add(p.image_id)
        for g in ground_truths:
            image_ids.add(g.image_id)
        total_images = len(image_ids)
        
        # 计算 mAP50
        pred_matched, gt_matched = self._match_predictions(
            predictions, ground_truths, iou_threshold=0.5
        )
        
        tp = sum(pred_matched)
        fp = len(predictions) - tp
        fn = len(ground_truths) - sum(gt_matched)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # 计算每个类别的 AP50
        ap50_list = []
        for class_id in range(self.num_classes):
            class_preds = [p for p in predictions if p.class_id == class_id]
            class_gts = [g for g in ground_truths if g.class_id == class_id]
            
            if not class_gts:
                continue
            
            # 按置信度排序
            class_preds.sort(key=lambda x: x.confidence, reverse=True)
            
            # 计算 PR 曲线
            precisions = []
            recalls = []
            tp_count = 0
            fp_count = 0
            
            matched_gts = set()
            for pred in class_preds:
                best_iou = 0
                best_gt_idx = -1
                
                for gt_idx, gt in enumerate(class_gts):
                    if gt_idx in matched_gts:
                        continue
                    if pred.image_id != gt.image_id:
                        continue
                    
                    iou = self._compute_iou(pred.bbox, gt.bbox)
                    if iou > best_iou and iou >= 0.5:
                        best_iou = iou
                        best_gt_idx = gt_idx
                
                if best_gt_idx >= 0:
                    tp_count += 1
                    matched_gts.add(best_gt_idx)
                else:
                    fp_count += 1
                
                p = tp_count / (tp_count + fp_count)
                r = tp_count / len(class_gts)
                precisions.append(p)
                recalls.append(r)
            
            ap = self._compute_ap(precisions, recalls)
            ap50_list.append(ap)
        
        mAP50 = np.mean(ap50_list) if ap50_list else 0.0
        
        # 计算 mAP50-95 (简化版本，使用多个 IoU 阈值)
        ap_list_all = []
        for iou_thresh in np.arange(0.5, 1.0, 0.05):
            for class_id in range(self.num_classes):
                class_preds = [p for p in predictions if p.class_id == class_id]
                class_gts = [g for g in ground_truths if g.class_id == class_id]
                
                if not class_gts:
                    continue
                
                class_preds.sort(key=lambda x: x.confidence, reverse=True)
                
                precisions = []
                recalls = []
                tp_count = 0
                fp_count = 0
                matched_gts = set()
                
                for pred in class_preds:
                    best_iou = 0
                    best_gt_idx = -1
                    
                    for gt_idx, gt in enumerate(class_gts):
                        if gt_idx in matched_gts:
                            continue
                        if pred.image_id != gt.image_id:
                            continue
                        
                        iou = self._compute_iou(pred.bbox, gt.bbox)
                        if iou > best_iou and iou >= iou_thresh:
                            best_iou = iou
                            best_gt_idx = gt_idx
                    
                    if best_gt_idx >= 0:
                        tp_count += 1
                        matched_gts.add(best_gt_idx)
                    else:
                        fp_count += 1
                    
                    p = tp_count / (tp_count + fp_count)
                    r = tp_count / len(class_gts)
                    precisions.append(p)
                    recalls.append(r)
                
                ap = self._compute_ap(precisions, recalls)
                ap_list_all.append(ap)
        
        mAP50_95 = np.mean(ap_list_all) if ap_list_all else 0.0
        
        return OverallMetrics(
            mAP50=float(mAP50),
            mAP50_95=float(mAP50_95),
            precision=float(precision),
            recall=float(recall),
            f1_score=float(f1_score),
            total_images=total_images,
            total_predictions=len(predictions),
            total_ground_truths=len(ground_truths),
        )
    
    def compute_per_class_metrics(
        self,
        predictions: List[Detection],
        ground_truths: List[Detection],
        iou_threshold: float = 0.5
    ) -> Dict[int, ClassMetrics]:
        """
        计算每个类别的指标
        
        Args:
            predictions: 预测结果列表
            ground_truths: 真实标签列表
            iou_threshold: IoU 阈值
            
        Returns:
            字典，键为类别 ID，值为 ClassMetrics
        """
        per_class_metrics = {}
        
        for class_id in range(self.num_classes):
            class_preds = [p for p in predictions if p.class_id == class_id]
            class_gts = [g for g in ground_truths if g.class_id == class_id]
            
            support = len(class_gts)
            
            if not class_gts:
                # 没有该类别的真实标签
                per_class_metrics[class_id] = ClassMetrics(
                    class_id=class_id,
                    class_name=self.class_names[class_id],
                    precision=0.0,
                    recall=0.0,
                    f1_score=0.0,
                    ap50=0.0,
                    ap50_95=0.0,
                    support=0,
                )
                continue
            
            # 按置信度排序
            class_preds.sort(key=lambda x: x.confidence, reverse=True)
            
            # 计算 AP50
            precisions = []
            recalls = []
            tp_count = 0
            fp_count = 0
            matched_gts = set()
            
            for pred in class_preds:
                best_iou = 0
                best_gt_idx = -1
                
                for gt_idx, gt in enumerate(class_gts):
                    if gt_idx in matched_gts:
                        continue
                    if pred.image_id != gt.image_id:
                        continue
                    
                    iou = self._compute_iou(pred.bbox, gt.bbox)
                    if iou > best_iou and iou >= 0.5:
                        best_iou = iou
                        best_gt_idx = gt_idx
                
                if best_gt_idx >= 0:
                    tp_count += 1
                    matched_gts.add(best_gt_idx)
                else:
                    fp_count += 1
                
                p = tp_count / (tp_count + fp_count)
                r = tp_count / len(class_gts)
                precisions.append(p)
                recalls.append(r)
            
            ap50 = self._compute_ap(precisions, recalls)
            
            # 计算最终的 precision, recall, f1
            final_precision = precisions[-1] if precisions else 0.0
            final_recall = recalls[-1] if recalls else 0.0
            f1 = 2 * final_precision * final_recall / (final_precision + final_recall) \
                if (final_precision + final_recall) > 0 else 0.0
            
            # 计算 AP50-95
            ap_list = []
            for iou_thresh in np.arange(0.5, 1.0, 0.05):
                precs = []
                recs = []
                tp_c = 0
                fp_c = 0
                matched = set()
                
                for pred in class_preds:
                    best_iou = 0
                    best_idx = -1
                    
                    for gt_idx, gt in enumerate(class_gts):
                        if gt_idx in matched:
                            continue
                        if pred.image_id != gt.image_id:
                            continue
                        
                        iou = self._compute_iou(pred.bbox, gt.bbox)
                        if iou > best_iou and iou >= iou_thresh:
                            best_iou = iou
                            best_idx = gt_idx
                    
                    if best_idx >= 0:
                        tp_c += 1
                        matched.add(best_idx)
                    else:
                        fp_c += 1
                    
                    p = tp_c / (tp_c + fp_c)
                    r = tp_c / len(class_gts)
                    precs.append(p)
                    recs.append(r)
                
                ap = self._compute_ap(precs, recs)
                ap_list.append(ap)
            
            ap50_95 = np.mean(ap_list) if ap_list else 0.0
            
            per_class_metrics[class_id] = ClassMetrics(
                class_id=class_id,
                class_name=self.class_names[class_id],
                precision=float(final_precision),
                recall=float(final_recall),
                f1_score=float(f1),
                ap50=float(ap50),
                ap50_95=float(ap50_95),
                support=support,
            )
        
        return per_class_metrics
    
    def compute_group_metrics(
        self,
        per_class_metrics: Dict[int, ClassMetrics]
    ) -> GroupMetrics:
        """
        计算行为组指标（正常行为 vs 预警行为）
        
        Args:
            per_class_metrics: 每类别指标字典
            
        Returns:
            GroupMetrics 包含正常行为和预警行为的分组指标
        """
        # 计算正常行为指标
        normal_metrics = [per_class_metrics[c] for c in self.NORMAL_CLASSES if c in per_class_metrics]
        if normal_metrics:
            normal_precision = np.mean([m.precision for m in normal_metrics])
            normal_recall = np.mean([m.recall for m in normal_metrics])
            normal_f1 = np.mean([m.f1_score for m in normal_metrics])
            normal_mAP50 = np.mean([m.ap50 for m in normal_metrics])
        else:
            normal_precision = normal_recall = normal_f1 = normal_mAP50 = 0.0
        
        # 计算预警行为指标
        warning_metrics = [per_class_metrics[c] for c in self.WARNING_CLASSES if c in per_class_metrics]
        if warning_metrics:
            warning_precision = np.mean([m.precision for m in warning_metrics])
            warning_recall = np.mean([m.recall for m in warning_metrics])
            warning_f1 = np.mean([m.f1_score for m in warning_metrics])
            warning_mAP50 = np.mean([m.ap50 for m in warning_metrics])
        else:
            warning_precision = warning_recall = warning_f1 = warning_mAP50 = 0.0
        
        return GroupMetrics(
            normal_precision=float(normal_precision),
            normal_recall=float(normal_recall),
            normal_f1=float(normal_f1),
            normal_mAP50=float(normal_mAP50),
            warning_precision=float(warning_precision),
            warning_recall=float(warning_recall),
            warning_f1=float(warning_f1),
            warning_mAP50=float(warning_mAP50),
        )
    
    def generate_confusion_matrix(
        self,
        predictions: List[Detection],
        ground_truths: List[Detection],
        normalize: bool = True
    ) -> np.ndarray:
        """
        生成混淆矩阵
        
        Args:
            predictions: 预测结果列表
            ground_truths: 真实标签列表
            normalize: 是否按行归一化
            
        Returns:
            混淆矩阵 numpy 数组，shape 为 (num_classes, num_classes)
        """
        # 初始化混淆矩阵
        cm = np.zeros((self.num_classes, self.num_classes), dtype=np.float64)
        
        # 按图像分组
        preds_by_image = defaultdict(list)
        gts_by_image = defaultdict(list)
        
        for pred in predictions:
            preds_by_image[pred.image_id].append(pred)
        
        for gt in ground_truths:
            gts_by_image[gt.image_id].append(gt)
        
        # 对每张图像进行匹配
        for image_id in set(preds_by_image.keys()) | set(gts_by_image.keys()):
            img_preds = preds_by_image.get(image_id, [])
            img_gts = gts_by_image.get(image_id, [])
            
            # 按置信度排序预测
            img_preds.sort(key=lambda x: x.confidence, reverse=True)
            
            matched_gts = set()
            
            for pred in img_preds:
                best_iou = 0
                best_gt_idx = -1
                best_gt = None
                
                for gt_idx, gt in enumerate(img_gts):
                    if gt_idx in matched_gts:
                        continue
                    
                    iou = self._compute_iou(pred.bbox, gt.bbox)
                    if iou > best_iou and iou >= 0.5:
                        best_iou = iou
                        best_gt_idx = gt_idx
                        best_gt = gt
                
                if best_gt is not None:
                    # 匹配成功，记录到混淆矩阵
                    cm[best_gt.class_id, pred.class_id] += 1
                    matched_gts.add(best_gt_idx)
            
            # 未匹配的真实标签（漏检）不计入混淆矩阵
            # 因为混淆矩阵主要关注分类错误，而非漏检
        
        # 按行归一化
        if normalize:
            row_sums = cm.sum(axis=1, keepdims=True)
            # 避免除以零
            row_sums[row_sums == 0] = 1
            cm = cm / row_sums
        
        return cm
    
    def analyze_confusion(
        self,
        confusion_matrix: np.ndarray,
        top_k: int = 3
    ) -> List[ConfusedPair]:
        """
        分析最容易混淆的类别对
        
        Args:
            confusion_matrix: 混淆矩阵（已归一化）
            top_k: 返回前 k 个最混淆的类别对
            
        Returns:
            ConfusedPair 列表
        """
        confused_pairs = []
        
        # 获取非对角线元素（混淆情况）
        n = confusion_matrix.shape[0]
        confusion_scores = []
        
        for i in range(n):
            for j in range(n):
                if i != j and confusion_matrix[i, j] > 0:
                    confusion_scores.append((i, j, confusion_matrix[i, j]))
        
        # 按混淆率排序
        confusion_scores.sort(key=lambda x: x[2], reverse=True)
        
        # 生成改进建议
        recommendations = {
            (0, 1): "举手和阅读容易混淆，建议增加举手动作的训练样本，特别是手臂位置明显的样本",
            (0, 2): "举手和书写容易混淆，建议关注手部位置特征的区分",
            (1, 2): "阅读和书写容易混淆，建议增加头部姿态和手部动作的区分特征",
            (1, 0): "阅读被误判为举手，建议增加阅读时低头姿态的样本",
            (2, 0): "书写被误判为举手，建议增加书写时手部位置的样本",
            (2, 1): "书写被误判为阅读，建议关注手部是否有书写动作",
            (3, 1): "睡觉被误判为阅读，建议增加睡觉时头部位置的特征",
            (3, 2): "睡觉被误判为书写，建议增加睡觉姿态的样本",
            (4, 0): "站立被误判为举手，建议关注全身姿态而非仅手部",
            (5, 1): "使用电子设备被误判为阅读，建议增加手持设备的特征",
            (5, 2): "使用电子设备被误判为书写，建议关注设备特征",
            (6, 1): "交谈被误判为阅读，建议增加多人互动的特征",
            (6, 4): "交谈被误判为站立，建议关注面部朝向和互动特征",
        }
        
        default_recommendation = "建议增加该类别的训练样本，并检查标注质量"
        
        for i, j, rate in confusion_scores[:top_k]:
            recommendation = recommendations.get(
                (i, j), 
                f"类别 {self.class_names_cn[i]} 容易被误判为 {self.class_names_cn[j]}，{default_recommendation}"
            )
            
            confused_pairs.append(ConfusedPair(
                class_a=i,
                class_a_name=self.class_names_cn[i],
                class_b=j,
                class_b_name=self.class_names_cn[j],
                confusion_rate=float(rate),
                recommendation=recommendation,
            ))
        
        return confused_pairs
