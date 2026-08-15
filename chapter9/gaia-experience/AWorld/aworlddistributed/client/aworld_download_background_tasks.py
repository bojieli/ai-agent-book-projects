import asyncio

from client.aworld_client import AworldTaskClient


async def download_with_timerange(know_hosts: list[str], start_time, end_time, save_path):
    # create client
    client = AworldTaskClient(know_hosts = know_hosts)

    # 1. download task results to file
    file_path = await client.download_task_results(
        start_time=start_time,
        end_time=end_time,
        save_path=save_path
    )

    # 2. parse local jsonl file
    local_results = client.parse_task_results_file(save_path)

    # 3. analyze results data
    for result in local_results:
        print(f"Submit User ID: {result['user_id']}, Task ID: {result['task_id']},Status: {result['status']}, Replays: {result['result_data']['replays_file'] if result['result_data'] else ''}")

if __name__ == '__main__':
    asyncio.run(download_with_timerange(know_hosts= ["http://localhost:9999"],
                    start_time="2025-06-12 00:00:00",
                    end_time="2025-06-12 23:59:59",
                    save_path="results/january_tasks.jsonl"))
