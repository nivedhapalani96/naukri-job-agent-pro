import argparse
from job_agent.core.app import AppContext
from job_agent.core.services import PollingService, DigestService
from job_agent.core.config import load_config, load_profile

def main():
    parser = argparse.ArgumentParser(prog="naukri-agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run scheduler (polling + digest)")
    p_run.add_argument("--config", required=True)

    p_once = sub.add_parser("poll-once", help="Run one polling cycle")
    p_once.add_argument("--config", required=True)
    p_once.add_argument("--no-email", action="store_true")

    p_mark = sub.add_parser("mark", help="Mark job status manually")
    p_mark.add_argument("--config", required=True)
    p_mark.add_argument("--job-key", required=True)
    p_mark.add_argument("--status", required=True, choices=["APPLIED", "SKIPPED", "MANUAL"])

    args = parser.parse_args()

    cfg = load_config(args.config)
    profile = load_profile(cfg.profile_path).profile
    ctx = AppContext.from_config(cfg)

    if args.cmd == "poll-once":
        PollingService(ctx, profile).run_once(send_email=not args.no_email)
    elif args.cmd == "mark":
        ctx.job_repo().mark_status(args.job_key, args.status)
    elif args.cmd == "run":
        ctx.scheduler().run(PollingService(ctx, profile), DigestService(ctx, profile))
