"""Streamlit dashboard for factor leaderboard, curves, IC timeline, regime panel, post-mortems."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import json

from ..memory.store import ExperimentStore
from ..viz.plots import (
    plot_equity_curve, plot_drawdown, plot_ic_timeline,
    plot_ic_histogram, plot_regime_heatmap, plot_factor_leaderboard
)


# Page config
st.set_page_config(
    page_title="Alpha-Mining Dashboard",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'store' not in st.session_state:
    st.session_state.store = ExperimentStore("experiments.db")


def check_backend_health():
    """Check if backend components are working.
    
    Returns:
        Tuple of (is_healthy, error_message)
    """
    try:
        # Test database connection
        store = st.session_state.store
        session = store.get_session()
        session.close()
        
        # Test basic imports
        from src.factors.dsl import DSLParser
        from src.backtest.metrics import sharpe
        
        return True, None
    except Exception as e:
        return False, str(e)


@st.cache_data
def load_runs_data():
    """Load runs data from database.
    
    Returns:
        DataFrame with runs data, or None if backend not healthy
    """
    try:
        store = st.session_state.store
        top_runs = store.get_top_runs(limit=100, order_by="sharpe")
        
        runs_data = []
        for run in top_runs:
            factor = store.get_factor(run.factor_id)
            metrics = run.metrics[0] if run.metrics else None
            
            if metrics:
                runs_data.append({
                    'run_id': run.id,
                    'factor_id': run.factor_id,
                    'factor_name': factor.name if factor else 'Unknown',
                    'sharpe': metrics.sharpe,
                    'maxdd': metrics.maxdd,
                    'avg_ic': metrics.avg_ic,
                    'ir': metrics.ir,
                    'turnover_monthly': metrics.turnover_monthly,
                    'ann_ret': metrics.ann_ret,
                    'ann_vol': metrics.ann_vol,
                    'hit_rate': metrics.hit_rate,
                    'regime': run.regime_label,
                    'start_date': run.start_date,
                    'end_date': run.end_date,
                    'n_issues': len(run.issues)
                })
        
        return pd.DataFrame(runs_data)
    except Exception as e:
        st.error(f"Error loading runs data: {e}")
        return pd.DataFrame()


def main():
    """Main dashboard function."""
    st.title("📈 Alpha-Mining LLM Agent Framework Dashboard")
    
    # Check backend health first
    is_healthy, error_msg = check_backend_health()
    
    if not is_healthy:
        st.error(f"⚠️ Backend not ready: {error_msg}")
        st.info("Please run backend tests first: `python scripts/test_backend.py`")
        st.stop()
    
    # Load data
    runs_df = load_runs_data()
    
    if len(runs_df) == 0:
        st.warning("No runs found in database. Run some backtests first!")
        st.info("Backend is healthy but no data available. Start by running factor discovery.")
        return
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    min_sharpe = st.sidebar.slider("Min Sharpe", 0.0, 3.0, 0.0, 0.1)
    max_maxdd = st.sidebar.slider("Max Drawdown", 0.0, 1.0, 1.0, 0.05)
    min_ic = st.sidebar.slider("Min Avg IC", -0.1, 0.2, -0.1, 0.01)
    
    # Apply filters
    filtered_df = runs_df[
        (runs_df['sharpe'] >= min_sharpe) &
        (abs(runs_df['maxdd']) <= max_maxdd) &
        (runs_df['avg_ic'] >= min_ic)
    ]
    
    # Real-time monitoring section
    st.sidebar.header("📊 Real-Time Monitoring")
    
    auto_refresh = st.sidebar.checkbox("Auto-refresh", False)
    refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 5, 60, 30)
    
    if auto_refresh:
        import time
        time.sleep(refresh_interval)
        st.rerun()
    
    # Pipeline status
    st.sidebar.header("Pipeline Status")
    pipeline_status = get_pipeline_status()
    st.sidebar.metric("Active Runs", pipeline_status.get('active_runs', 0))
    st.sidebar.metric("Pending", pipeline_status.get('pending', 0))
    st.sidebar.metric("Completed Today", pipeline_status.get('completed_today', 0))
    
    # Learning metrics
    st.sidebar.header("Learning Metrics")
    learning_metrics = get_learning_metrics()
    st.sidebar.metric("Knowledge Base Size", learning_metrics.get('kb_size', 0))
    st.sidebar.metric("Success Rate", f"{learning_metrics.get('success_rate', 0):.1%}")
    st.sidebar.metric("Error Bank Entries", learning_metrics.get('error_bank_size', 0))
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Leaderboard", "Performance", "IC Analysis", "Regime Analysis", "Post-Mortems", "Monitoring"
    ])
    
    with tab1:
        st.header("Factor Leaderboard")
        
        # Sort options
        sort_by = st.selectbox("Sort by", ["sharpe", "avg_ic", "ir", "ann_ret"], index=0)
        ascending = st.checkbox("Ascending", False)
        
        display_df = filtered_df.sort_values(sort_by, ascending=ascending)
        
        # Display table
        st.dataframe(
            display_df[['factor_name', 'sharpe', 'maxdd', 'avg_ic', 'ir', 
                       'turnover_monthly', 'ann_ret', 'ann_vol', 'hit_rate', 'n_issues']].head(20),
            use_container_width=True
        )
        
        # Leaderboard chart
        if len(display_df) > 0:
            leaderboard_data = display_df.head(10).to_dict('records')
            fig = plot_factor_leaderboard(leaderboard_data)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.header("Performance Analysis")
        
        if len(filtered_df) == 0:
            st.warning("No runs match the filters.")
        else:
            # Select run
            run_options = filtered_df['factor_name'].tolist()
            selected_factor = st.selectbox("Select Factor", run_options, index=0)
            
            selected_run = filtered_df[filtered_df['factor_name'] == selected_factor].iloc[0]
            run_id = selected_run['run_id']
            
            # Load equity curve if available
            run_dir = Path(f"experiments/runs/run_{run_id}")
            equity_file = run_dir / "equity_curve.parquet"
            
            if equity_file.exists():
                equity_curve = pd.read_parquet(equity_file)['equity']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = plot_equity_curve(equity_curve, title=f"Equity Curve: {selected_factor}")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    fig = plot_drawdown(equity_curve, title=f"Drawdown: {selected_factor}")
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Equity curve data not available for this run.")
            
            # Metrics summary
            st.subheader("Metrics Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Sharpe Ratio", f"{selected_run['sharpe']:.2f}")
                st.metric("Max Drawdown", f"{selected_run['maxdd']:.2%}")
            
            with col2:
                st.metric("Avg IC", f"{selected_run['avg_ic']:.4f}")
                st.metric("Information Ratio", f"{selected_run['ir']:.2f}")
            
            with col3:
                st.metric("Ann Return", f"{selected_run['ann_ret']:.2%}")
                st.metric("Ann Volatility", f"{selected_run['ann_vol']:.2%}")
            
            with col4:
                st.metric("Turnover (monthly)", f"{selected_run['turnover_monthly']:.1f}%")
                st.metric("Hit Rate", f"{selected_run['hit_rate']:.2%}")
    
    with tab3:
        st.header("Information Coefficient Analysis")
        
        if len(filtered_df) == 0:
            st.warning("No runs match the filters.")
        else:
            selected_factor = st.selectbox("Select Factor", filtered_df['factor_name'].tolist(), 
                                         key="ic_factor", index=0)
            selected_run = filtered_df[filtered_df['factor_name'] == selected_factor].iloc[0]
            run_id = selected_run['run_id']
            
            # IC timeline (simplified - would need IC series data)
            st.info("IC timeline would be displayed here if IC series data is available.")
            
            # IC statistics
            st.subheader("IC Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Average IC", f"{selected_run['avg_ic']:.4f}")
            
            with col2:
                st.metric("Information Ratio", f"{selected_run['ir']:.2f}")
            
            with col3:
                # Would calculate IC std if available
                st.metric("IC Quality", "Good" if selected_run['avg_ic'] > 0.05 else "Needs Improvement")
    
    with tab4:
        st.header("Regime Analysis")
        
        if len(filtered_df) == 0:
            st.warning("No runs match the filters.")
        else:
            # Group by regime
            regime_df = filtered_df.groupby('regime').agg({
                'sharpe': 'mean',
                'avg_ic': 'mean',
                'ann_ret': 'mean',
                'maxdd': 'mean'
            }).reset_index()
            
            if len(regime_df) > 0:
                st.dataframe(regime_df, use_container_width=True)
                
                # Regime heatmap
                performance_by_regime = {}
                for _, row in regime_df.iterrows():
                    performance_by_regime[row['regime'] or 'unknown'] = {
                        'sharpe': row['sharpe'],
                        'avg_ic': row['avg_ic'],
                        'return': row['ann_ret'],
                        'maxdd': abs(row['maxdd'])
                    }
                
                fig = plot_regime_heatmap(performance_by_regime)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No regime data available.")
    
    with tab5:
        st.header("Post-Mortems & Lessons")
        
        store = st.session_state.store
        
        # Get lessons
        from ..memory.lessons import LessonManager
        lesson_manager = LessonManager(store)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Success Stories")
            success_lessons = lesson_manager.get_success_ledger(limit=10)
            
            for lesson in success_lessons:
                with st.expander(f"✓ {lesson.title}"):
                    st.write(lesson.body[:500] + "...")
                    st.caption(f"Tags: {', '.join(lesson.tags or [])}")
        
        with col2:
            st.subheader("Failure Analysis")
            failure_lessons = lesson_manager.get_error_bank(limit=10)
            
            for lesson in failure_lessons:
                with st.expander(f"✗ {lesson.title}"):
                    st.write(lesson.body[:500] + "...")
                    st.caption(f"Tags: {', '.join(lesson.tags or [])}")
        
        # Run details
        st.subheader("Run Details")
        selected_run_id = st.selectbox(
            "Select Run ID",
            filtered_df['run_id'].tolist(),
            key="postmortem_run"
        )
        
        if selected_run_id:
            run = store.get_session().query(store.Run).filter(store.Run.id == selected_run_id).first()
            if run:
                factor = store.get_factor(run.factor_id)
                metrics = run.metrics[0] if run.metrics else None
                issues = run.issues
                
                st.write(f"**Factor:** {factor.name if factor else 'Unknown'}")
                st.write(f"**Date Range:** {run.start_date.date()} to {run.end_date.date()}")
                
                if metrics:
                    st.write(f"**Sharpe:** {metrics.sharpe:.2f}")
                    st.write(f"**MaxDD:** {metrics.maxdd:.2%}")
                
                if issues:
                    st.write("**Issues:**")
                    for issue in issues:
                        st.write(f"- **{issue.type}** ({issue.severity}): {issue.detail}")
    
    with tab6:
        st.header("Real-Time Monitoring")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Iteration Progress")
            iteration_progress = get_iteration_progress()
            
            if iteration_progress:
                st.metric("Current Iteration", iteration_progress.get('iteration', 0))
                st.metric("Candidates Generated", iteration_progress.get('candidates', 0))
                st.metric("In Progress", iteration_progress.get('in_progress', 0))
                st.metric("Completed", iteration_progress.get('completed', 0))
            else:
                st.info("No active iterations")
        
        with col2:
            st.subheader("Factor Pipeline Status")
            pipeline_status = get_pipeline_status()
            
            # Status breakdown
            status_df = pd.DataFrame([
                {'Status': 'Pending', 'Count': pipeline_status.get('pending', 0)},
                {'Status': 'Running', 'Count': pipeline_status.get('running', 0)},
                {'Status': 'Completed', 'Count': pipeline_status.get('completed', 0)},
                {'Status': 'Failed', 'Count': pipeline_status.get('failed', 0)}
            ])
            
            st.bar_chart(status_df.set_index('Status'))
        
        st.subheader("Learning Metrics Over Time")
        learning_timeline = get_learning_timeline()
        
        if learning_timeline and len(learning_timeline) > 0:
            timeline_df = pd.DataFrame(learning_timeline)
            st.line_chart(timeline_df.set_index('date')[['success_rate', 'kb_size']])
        else:
            st.info("No historical learning data available")
        
        st.subheader("Recent Activity")
        recent_activity = get_recent_activity(limit=10)
        
        if recent_activity:
            for activity in recent_activity:
                with st.expander(f"{activity['timestamp']} - {activity['type']}"):
                    st.write(activity['description'])
        else:
            st.info("No recent activity")


def get_pipeline_status():
    """Get current pipeline status."""
    store = st.session_state.store
    session = store.get_session()
    try:
        pending = session.query(store.Run).filter(store.Run.status == 'pending').count()
        running = session.query(store.Run).filter(store.Run.status == 'running').count()
        completed = session.query(store.Run).filter(store.Run.status == 'completed').count()
        failed = session.query(store.Run).filter(store.Run.status == 'failed').count()
        
        return {
            'pending': pending,
            'running': running,
            'completed': completed,
            'failed': failed,
            'active_runs': pending + running,
            'completed_today': completed  # Simplified
        }
    finally:
        session.close()


def get_learning_metrics():
    """Get learning metrics."""
    store = st.session_state.store
    from ..memory.lessons import LessonManager
    
    lesson_manager = LessonManager(store)
    
    success_lessons = lesson_manager.get_success_ledger(limit=1000)
    failure_lessons = lesson_manager.get_error_bank(limit=1000)
    
    total_runs = len(store.get_top_runs(limit=1000))
    success_count = len([r for r in store.get_top_runs(limit=1000) 
                        if r.metrics and r.metrics[0].sharpe >= 1.0])
    
    success_rate = success_count / total_runs if total_runs > 0 else 0.0
    
    return {
        'kb_size': len(success_lessons) + len(failure_lessons),
        'success_rate': success_rate,
        'error_bank_size': len(failure_lessons),
        'success_ledger_size': len(success_lessons)
    }


def get_iteration_progress():
    """Get current iteration progress."""
    # This would track active iterations
    # For now, return mock data
    return {
        'iteration': 1,
        'candidates': 3,
        'in_progress': 1,
        'completed': 2
    }


def get_learning_timeline():
    """Get learning metrics over time."""
    # This would query historical data
    # For now, return empty
    return []


def get_recent_activity(limit=10):
    """Get recent activity log."""
    store = st.session_state.store
    session = store.get_session()
    try:
        recent_runs = session.query(store.Run).order_by(
            store.Run.created_at.desc()
        ).limit(limit).all()
        
        activities = []
        for run in recent_runs:
            factor = store.get_factor(run.factor_id)
            activities.append({
                'timestamp': run.created_at.strftime('%Y-%m-%d %H:%M'),
                'type': 'Run Completed',
                'description': f"Factor: {factor.name if factor else 'Unknown'}, Status: {run.status}"
            })
        
        return activities
    finally:
        session.close()


if __name__ == "__main__":
    main()

