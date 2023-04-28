import requests
import json
import os
from typing import Tuple, Optional
import mimetypes
import uuid
import zipfile

API_URL = "https://api.ragdoll.ai/graphql"

API_KEY = os.getenv("RAGDOLL_API_KEY")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
}

def get_user_owner_id() -> Optional[int]:
    query = """
    query MyInfo {
        myInfo {
            id
        }
    }
    """

    try:
        response = requests.post(API_URL, json={"query": query}, headers=headers)
        response_data = response.json()
    except json.decoder.JSONDecodeError:
        print("Error: Invalid JSON response received from the server.")
        return None

    if "data" in response_data and "myInfo" in response_data["data"]:
        owner_id = response_data["data"]["myInfo"]["id"]
        return owner_id
    else:
        print("Error: Failed to get user owner ID.")
        return None

owner_id = get_user_owner_id()

def zip_directory(directory_path: str, zip_path: str):
    """
    Zips the contents of a directory and saves the zip file to the specified path.

    Args:
        directory_path (str): The path of the directory to be zipped.
        zip_path (str): The path where the zip file will be saved.
    """
    # Check if the directory exists
    if not os.path.exists(directory_path):
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    # Create a ZipFile object in write mode
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Iterate through the directory
        for root, _, files in os.walk(directory_path):
            for file in files:
                # Construct the file path
                file_path = os.path.join(root, file)
                # Add the file to the zip file
                zip_file.write(file_path, os.path.relpath(file_path, directory_path))

def zip_files(file_paths: list, zip_path: str):
    """
    Zips the specified files and saves the zip file to the specified path.

    Args:
        file_paths (list): A list of file paths to be zipped.
        zip_path (str): The path where the zip file will be saved.
    """
    # Create a ZipFile object in write mode
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Iterate through the file paths
        for file_path in file_paths:
            # Check if the file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Add the file to the zip file
            zip_file.write(file_path, os.path.basename(file_path))

def submit_text(task_id: int, content: str) -> Tuple[int, str]:
    query = """
    mutation CreateSubmission($input: SubmissionInput!) {
        createSubmission(input: $input) {
            id
            content
        }
    }
    """

    variables = {
        "input": {
            "ownerId": owner_id,
            "taskId": str(task_id),
            "type": "Text",
            "content": content,
        }
    }

    response = requests.post(API_URL, json={"query": query, "variables": variables}, headers=headers)
    response_data = response.json()
    print(response_data)
    submission_id = response_data["data"]["createSubmission"]["id"]
    submission_content = response_data["data"]["createSubmission"]["content"]

    return submission_id, submission_content


def submit_file(task_id: int, file_path: str) -> int:
    query = """
    mutation CreateSubmission($input: SubmissionInput!, $file: Upload!) {
        createSubmission(input: $input, file: $file) {
            id
        }
    }
    """

    variables = {
        "input": {
            "ownerId": owner_id,
            "taskId": str(task_id),
            "type": "File",
        },
    }

    with open(file_path, "rb") as f:
        file_data = f.read()

    file_mimetype = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    file_name = os.path.basename(file_path)

    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    file_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }
    file_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"

    data = f"--{boundary}\r\nContent-Disposition: form-data; name=\"operations\"\r\n\r\n{json.dumps({'query': query, 'variables': variables})}\r\n"
    data += f"--{boundary}\r\nContent-Disposition: form-data; name=\"map\"\r\n\r\n{json.dumps({'file': ['variables.file']})}\r\n"
    data += f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{file_name}\"\r\nContent-Type: {file_mimetype}\r\n\r\n"
    data = data.encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

    response = requests.post(API_URL, data=data, headers=file_headers)
    response_data = response.json()
    print(response_data)
    submission_id = response_data["data"]["createSubmission"]["id"]
    return submission_id

def submit_file_input(input_data, task_id: int):
    if isinstance(input_data, str):
        if os.path.isdir(input_data):
            # Zip the directory and submit
            zip_path = f"{os.path.basename(input_data)}.zip"
            zip_directory(input_data, zip_path)
            submission_id = submit_file(owner_id, task_id, zip_path)
            print(f"Zipped directory submission created for task {task_id} with ID {submission_id} and filename '{zip_path}'")
        elif os.path.isfile(input_data):
            # Submit the file directly
            submission_id = submit_file(owner_id, task_id, input_data)
            print(f"File submission created for task {task_id} with ID {submission_id} and filename '{input_data}'")
        else:
            raise ValueError("Invalid input: Not a file or directory")
    elif isinstance(input_data, list):
        # Zip the list of files and submit
        zip_path = "files.zip"
        zip_files(input_data, zip_path)
        submission_id = submit_file(owner_id, task_id, zip_path)
        print(f"Zipped files submission created for task {task_id} with ID {submission_id} and filename '{zip_path}'")
    else:
        raise ValueError("Invalid input: Must be a string or a list")


def has_submission_for_task(task_id: int) -> bool:
    query = """
    query SubmissionsForTask($taskId: ID!) {
        submissionsForTask(taskId: $taskId) {
            id
            owner {
                id
            }
        }
    }
    """

    variables = {
        "taskId": task_id,
    }

    response = requests.post(API_URL, json={"query": query, "variables": variables}, headers=headers)
    response_data = response.json()

    submissions = response_data["data"]["submissionsForTask"]

    for submission in submissions:
        if submission["owner"]["id"] == owner_id:
            return True

    return False


def get_all_tasks() -> list:
    query = """
    query Tasks {
        tasks {
            id
        }
    }
    """

    response = requests.post(API_URL, json={"query": query}, headers=headers)
    response_data = response.json()

    tasks = response_data["data"]["tasks"]

    return tasks

def get_open_tasks() -> list:
    query = """
    query OpenTasks {
        openTasks {
            id
            owner {
                id
            }
        }
    }
    """

    response = requests.post(API_URL, json={"query": query}, headers=headers)
    print(response)

    try:
        response_data = response.json()
    except json.decoder.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return []

    tasks = response_data["data"]["openTasks"]
    return tasks

def get_task_details(task_id: int) -> dict:
    query = """
    query Task($id: ID!) {
        task(id: $id) {
            id
            name
            description
            expectedOutput
            outputType
            owner {
                id
            }
        }
    }
    """

    variables = {
        "id": task_id,
    }

    response = requests.post(API_URL, json={"query": query, "variables": variables}, headers=headers)
    response_data = response.json()
    task = response_data["data"]["task"]

    return task

def create_task(name: str, description: str, budget: str, expected_output: str, output_type: str) -> dict:
    """Hire an AI Agent to complete task
    Args:
        name (str): The name of the task
        description (str): The description of the task
        budget (float): The budget of the task, keep this under $1
        expected_output (str): The expected output of the task
        output_type (str): The type of output, either "Text" or "File"

    Returns:
        dict: the json response from the API
    """
    if output_type != "Text" and output_type != "File":
        raise ValueError("Invalid output type: Must be either 'Text' for a text output or 'File' for any other type of output (case sensitive)")

    query = """
    mutation CreateTask($input: TaskInput!) {
        createTask(input: $input) {
            id
            name
            description
            budget
            expectedOutput
            outputType
        }
    }
    """

    variables = {
        "input": {
            "ownerId": owner_id,
            "name": name,
            "description": description,
            "budget": float(budget),
            "expectedOutput": expected_output,
            "outputType": output_type,
        }
    }

    response = requests.post(API_URL, json={"query": query, "variables": variables}, headers=headers)
    response_data = response.json()
    task = response_data["data"]["createTask"]

    return task

def get_submissions_for_task(task_id: int) -> list:
    query = """
    query SubmissionsForTask($taskId: ID!) {
        submissionsForTask(taskId: $taskId) {
            id
            owner {
                id
            }
            task {
                id
                name
                description
                expectedOutput
                outputType
            }
            type
            content
            file
        }
    }
    """

    variables = {
        "taskId": task_id,
    }

    response = requests.post(API_URL, json={"query": query, "variables": variables}, headers=headers)
    response_data = response.json()
    submissions = response_data["data"]["submissionsForTask"]

    return submissions

def close_task(task_id: int, accepted_submission_id: int) -> dict:
    query = """
    mutation CloseTask($taskId: ID!, $acceptedSubmissionId: ID!) {
        closeTask(taskId: $taskId, acceptedSubmissionId: $acceptedSubmissionId) {
            id
            status
        }
    }
    """

    variables = {
        "taskId": task_id,
        "acceptedSubmissionId": accepted_submission_id,
    }

    response = requests.post(API_URL, json={"query": query, "variables": variables}, headers=headers)
    response_data = response.json()
    task = response_data["data"]["closeTask"]

    return task