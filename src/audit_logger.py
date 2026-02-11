import json
import os
from datetime import datetime
import hashlib

class AuditLogger:
    """
    Tracks all mockup generation activities for audit trail and history.
    """
    
    def __init__(self, log_dir='logs'):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, 'generation_history.jsonl')
        self.current_session = None
        self.logs = []
    
    def start_session(self, measure_name, testcase_path, vsd_path, user=None):
        """Start a new generation session."""
        self.current_session = {
            'session_id': self._generate_session_id(),
            'measure': measure_name,
            'timestamp_start': datetime.now().isoformat(),
            'testcase_file': os.path.basename(testcase_path),
            'testcase_hash': self._hash_file(testcase_path),
            'vsd_file': os.path.basename(vsd_path),
            'user': user or os.getenv('USERNAME', 'unknown'),
            'status': 'started',
            'events': []
        }
        
        print(f"📝 Audit Session Started: {self.current_session['session_id']}")
        return self.current_session['session_id']
    
    def log_event(self, event_type, message, details=None):
        """Log an event in the current session."""
        if not self.current_session:
            return
        
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'message': message,
            'details': details or {}
        }
        
        self.current_session['events'].append(event)
    
    def log_parsing(self, scenario_count, ai_fallback_count=0):
        """Log parsing statistics."""
        self.log_event('parsing', f'Parsed {scenario_count} scenarios', {
            'total_scenarios': scenario_count,
            'ai_fallback_used': ai_fallback_count,
            'ai_fallback_rate': (ai_fallback_count / scenario_count * 100) if scenario_count > 0 else 0
        })
    
    def log_generation(self, member_count, record_counts):
        """Log generation statistics."""
        total_records = sum(record_counts.values())
        
        self.log_event('generation', f'Generated data for {member_count} members', {
            'member_count': member_count,
            'total_records': total_records,
            'records_by_table': record_counts
        })
    
    def log_quality_check(self, quality_report):
        """Log quality check results."""
        self.log_event('quality_check', 'Data quality validation completed', {
            'passed': quality_report['passed'],
            'total_issues': quality_report['total_issues'],
            'total_warnings': quality_report['total_warnings'],
            'stats': quality_report.get('stats', {})
        })
    
    def log_validation(self, validation_summary):
        """Log validation results."""
        self.log_event('validation', 'Expected results validation completed', {
            'total_cases': validation_summary['total'],
            'passed': validation_summary['passed'],
            'failed': validation_summary['failed'],
            'pass_rate': validation_summary['pass_rate']
        })
    
    def end_session(self, output_path, success=True, error=None):
        """End the current session and save to log."""
        if not self.current_session:
            return
        
        self.current_session['timestamp_end'] = datetime.now().isoformat()
        self.current_session['status'] = 'success' if success else 'failed'
        self.current_session['output_file'] = os.path.basename(output_path) if output_path else None
        
        if output_path and os.path.exists(output_path):
            self.current_session['output_hash'] = self._hash_file(output_path)
            self.current_session['output_size_mb'] = os.path.getsize(output_path) / (1024 * 1024)
        
        if error:
            self.current_session['error'] = str(error)
        
        # Calculate duration
        start = datetime.fromisoformat(self.current_session['timestamp_start'])
        end = datetime.fromisoformat(self.current_session['timestamp_end'])
        self.current_session['duration_seconds'] = (end - start).total_seconds()
        
        # Save to log file
        self._save_session()
        
        status_icon = "✅" if success else "❌"
        print(f"{status_icon} Audit Session Ended: {self.current_session['session_id']}")
        
        self.current_session = None
    
    def log(self, level, message):
        from src.progress import progress_tracker
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {level.upper()}: {message}"
        self.logs.append(log_entry)
        
        # Real-time UI feed
        progress_tracker.update(f"🛡️ {level.upper()}: {message}")
        
        print(log_entry)
    
    def _generate_session_id(self):
        """Generate unique session ID."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_suffix = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:6]
        return f"{timestamp}_{random_suffix}"
    
    def _hash_file(self, file_path):
        """Generate MD5 hash of file for integrity checking."""
        if not os.path.exists(file_path):
            return None
        
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return None
    
    def _save_session(self):
        """Save session to JSONL log file."""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(self.current_session) + '\n')
    
    def get_history(self, limit=10, measure=None):
        """
        Retrieve generation history.
        
        Args:
            limit: Maximum number of sessions to return
            measure: Filter by measure name
        
        Returns:
            List of session dicts
        """
        if not os.path.exists(self.log_file):
            return []
        
        sessions = []
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    session = json.loads(line.strip())
                    if measure and session.get('measure') != measure:
                        continue
                    sessions.append(session)
                except:
                    continue
        
        # Return most recent first
        return sorted(sessions, key=lambda x: x['timestamp_start'], reverse=True)[:limit]
    
    def get_statistics(self, days=30):
        """
        Get aggregate statistics for the last N days.
        
        Returns:
            Dict with statistics
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        sessions = self.get_history(limit=1000)
        recent_sessions = [
            s for s in sessions 
            if datetime.fromisoformat(s['timestamp_start']).timestamp() > cutoff
        ]
        
        if not recent_sessions:
            return {
                'total_generations': 0,
                'success_rate': 0,
                'avg_duration_seconds': 0,
                'measures': {},
                'total_members_generated': 0
            }
        
        total = len(recent_sessions)
        successful = sum(1 for s in recent_sessions if s['status'] == 'success')
        
        durations = [s.get('duration_seconds', 0) for s in recent_sessions if s.get('duration_seconds')]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Count by measure
        measures = {}
        for s in recent_sessions:
            measure = s.get('measure', 'unknown')
            measures[measure] = measures.get(measure, 0) + 1
        
        # Total members generated
        total_members = 0
        for s in recent_sessions:
            for event in s.get('events', []):
                if event['type'] == 'generation':
                    total_members += event.get('details', {}).get('member_count', 0)
        
        return {
            'total_generations': total,
            'successful_generations': successful,
            'failed_generations': total - successful,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'avg_duration_seconds': avg_duration,
            'measures': measures,
            'total_members_generated': total_members,
            'period_days': days
        }
    
    def export_summary(self, output_path, days=30):
        """Export summary report to JSON."""
        stats = self.get_statistics(days)
        history = self.get_history(limit=100)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'period_days': days,
            'statistics': stats,
            'recent_history': history
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Audit summary exported: {output_path}")

if __name__ == "__main__":
    # Example usage
    logger = AuditLogger()
    
    # Show statistics
    stats = logger.get_statistics(days=30)
    print("\n📊 Generation Statistics (Last 30 Days):")
    print(f"   Total Generations: {stats['total_generations']}")
    print(f"   Success Rate: {stats['success_rate']:.1f}%")
    print(f"   Avg Duration: {stats['avg_duration_seconds']:.1f}s")
    print(f"   Total Members: {stats['total_members_generated']}")
    
    # Show recent history
    history = logger.get_history(limit=5)
    if history:
        print("\n📜 Recent Generations:")
        for session in history:
            status = "✅" if session['status'] == 'success' else "❌"
            print(f"   {status} {session['timestamp_start'][:19]} - {session['measure']} ({session.get('duration_seconds', 0):.1f}s)")
