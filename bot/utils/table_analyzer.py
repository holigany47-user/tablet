import pandas as pd
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class TableAnalyzer:
    """Анализатор для сравнения таблиц и выявления различий"""
    
    @staticmethod
    def analyze_tables_diff(old_df: pd.DataFrame, new_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Анализирует различия между двумя таблицами
        """
        logger.info("🔍 Анализ различий между таблицами")
        
        try:
            # Анализ столбцов
            old_columns = set(old_df.columns)
            new_columns = set(new_df.columns)
            
            added_columns = list(new_columns - old_columns)
            removed_columns = list(old_columns - new_columns)
            common_columns = list(old_columns & new_columns)
            
            # Анализ строк (используем хеши для сравнения)
            old_df_hash = old_df.astype(str).sum(axis=1).apply(hash)
            new_df_hash = new_df.astype(str).sum(axis=1).apply(hash)
            
            old_hashes = set(old_df_hash)
            new_hashes = set(new_df_hash)
            
            added_rows = len(new_hashes - old_hashes)
            removed_rows = len(old_hashes - new_hashes)
            common_rows = len(old_hashes & new_hashes)
            
            # Анализ измененных данных в общих столбцах
            changed_data = []
            if common_columns:
                common_df_old = old_df[common_columns].reset_index(drop=True)
                common_df_new = new_df[common_columns].reset_index(drop=True)
                
                # Сравниваем построчно
                for idx in range(min(len(common_df_old), len(common_df_new))):
                    for col in common_columns:
                        old_val = common_df_old.at[idx, col]
                        new_val = common_df_new.at[idx, col]
                        
                        if pd.notna(old_val) and pd.notna(new_val) and old_val != new_val:
                            changed_data.append({
                                'row_index': idx,
                                'column': col,
                                'old_value': str(old_val),
                                'new_value': str(new_val)
                            })
                        elif pd.isna(old_val) and pd.notna(new_val):
                            changed_data.append({
                                'row_index': idx,
                                'column': col,
                                'old_value': 'NULL',
                                'new_value': str(new_val)
                            })
                        elif pd.notna(old_val) and pd.isna(new_val):
                            changed_data.append({
                                'row_index': idx,
                                'column': col,
                                'old_value': str(old_val),
                                'new_value': 'NULL'
                            })
            
            analysis_result = {
                'columns': {
                    'added': added_columns,
                    'removed': removed_columns,
                    'common': common_columns,
                    'total_old': len(old_columns),
                    'total_new': len(new_columns)
                },
                'rows': {
                    'added': added_rows,
                    'removed': removed_rows,
                    'common': common_rows,
                    'total_old': len(old_df),
                    'total_new': len(new_df)
                },
                'changes': changed_data,
                'summary': {
                    'has_changes': len(added_columns) > 0 or len(removed_columns) > 0 or added_rows > 0 or removed_rows > 0 or len(changed_data) > 0
                }
            }
            
            logger.info(f"✅ Анализ завершен: {analysis_result['summary']}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при анализе таблиц: {e}")
            return {
                'columns': {'added': [], 'removed': [], 'common': [], 'total_old': 0, 'total_new': 0},
                'rows': {'added': 0, 'removed': 0, 'common': 0, 'total_old': 0, 'total_new': 0},
                'changes': [],
                'summary': {'has_changes': False},
                'error': str(e)
            }
    
    @staticmethod
    def format_analysis_report(analysis: Dict[str, Any]) -> str:
        """Форматирует отчет об анализе для пользователя"""
        if analysis.get('error'):
            return f"❌ Ошибка анализа: {analysis['error']}"
        
        report = [
            "🔍 **АНАЛИЗ РАЗЛИЧИЙ МЕЖДУ ТАБЛИЦАМИ**",
            "",
            f"📊 **СТАРАЯ**: {analysis['rows']['total_old']} строк, {analysis['columns']['total_old']} колонок",
            f"📈 **НОВАЯ**: {analysis['rows']['total_new']} строк, {analysis['columns']['total_new']} колонок",
            "",
            "📋 **РАЗЛИЧИЯ В СТОЛБЦАХ:**"
        ]
        
        if analysis['columns']['added']:
            report.append(f"• ✅ Добавлено: {len(analysis['columns']['added'])}")
            for col in analysis['columns']['added'][:5]:  # Показываем первые 5
                report.append(f"  └ {col}")
            if len(analysis['columns']['added']) > 5:
                report.append(f"  └ ... и еще {len(analysis['columns']['added']) - 5}")
        else:
            report.append("• ✅ Новых столбцов нет")
        
        if analysis['columns']['removed']:
            report.append(f"• ❌ Удалено: {len(analysis['columns']['removed'])}")
        else:
            report.append("• ❌ Удаленных столбцов нет")
            
        report.append(f"• 🔄 Общие: {len(analysis['columns']['common'])}")
        
        report.extend([
            "",
            "📈 **РАЗЛИЧИЯ В СТРОКАХ:**",
            f"• ✅ Новых строк: {analysis['rows']['added']}",
            f"• ❌ Удаленных строк: {analysis['rows']['removed']}",
            f"• 🔄 Общих строк: {analysis['rows']['common']}",
        ])
        
        if analysis['changes']:
            report.extend([
                "",
                f"⚡ **ИЗМЕНЕННЫЕ ДАННЫЕ**: {len(analysis['changes'])} значений"
            ])
        
        return "\n".join(report)
