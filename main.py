import datetime
import argparse
from dateutil import parser as date_parser
import gitlab
from collections import defaultdict
from tqdm import tqdm


def parse_project(project, back_date, debug):
    mr_review_count = defaultdict(int)
    mr_count = defaultdict(int)
    mrs = project.mergerequests.list(iterator=True)
    for mr in tqdm(mrs):
        mr_user = mr.author["username"]
        review_users = set()
        approval_user = mr.approvals.get().approved_by
        mr_date = date_parser.isoparse(mr.created_at)
        for i in mr.notes.list(get_all=True):
            review_users.add(i.author["username"])

        for j in approval_user:
            review_users.add(j["user"]["username"])

        if debug:
            print(f"{mr_user}<-{review_users}")

        mr_count[mr_user] += 1
        for each_user in review_users:
            mr_review_count[each_user] += 1

        if back_date > mr_date:
            break

    return dict(mr_count), dict(mr_review_count)


def read_project(url, token, projects, back_date, debug):
    mr_count = {}
    mr_review_count = {}

    back_date = back_date.astimezone(datetime.timezone.utc)
    gl = gitlab.Gitlab(url, private_token=token)

    for project in projects:
        gl_project = gl.projects.get(project)
        project_mr_count, project_mr_review_count = parse_project(
            gl_project, back_date, debug
        )

        print(f"\n----project {gl_project.name} result:")
        print(f"{project_mr_count=}\n{project_mr_review_count=}")

        mr_count.update(project_mr_count)
        mr_review_count.update(project_mr_review_count)

    print(f"\n----total result:")
    print(f"{mr_count=}\n{mr_review_count=}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="获取gitlab仓库一段时间内的commit数量与参与的MR数量")
    parser.add_argument("projects", type=int, nargs="+", help="需要统计的仓库id")
    parser.add_argument(
        "--url",
        "-U",
        help="gitlab URL",
    )
    parser.add_argument(
        "--token",
        "-T",
        help="private token",
        required=True,
    )
    parser.add_argument(
        "--date",
        "-D",
        help="截止日期,使用 isoformat，比如2023-05-14",
        type=date_parser.isoparse,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
    )

    args = parser.parse_args()
    read_project(args.url, args.token, args.projects, args.date, args.debug)
