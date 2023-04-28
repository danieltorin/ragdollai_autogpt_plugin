# Ragdoll.ai AutoGPT plugin
A starting point for enabling AutoGPT to connect to ragdoll.ai

### Plugin Installation Steps

1. **Clone or download the plugin repository:**
   Clone the plugin repository, or download the repository as a zip file.

2. **Install the plugin's dependencies (if any):**
   Navigate to the plugin's folder in your terminal, and run the following command to install any required dependencies:

   ``` shell
      pip install -r requirements.txt
   ```

3. **Package the plugin as a Zip file:**
   If you cloned the repository, compress the plugin folder as a Zip file.

4. **Copy the plugin's Zip file:**
   Place the plugin's Zip file in the `plugins` folder of the Auto-GPT repository.

5. **Allowlist the plugin (optional):**
   Add the plugin's class name to the `ALLOWLISTED_PLUGINS` in the `.env` file to avoid being prompted with a warning when loading the plugin:

   ``` shell
   ALLOWLISTED_PLUGINS=AutoGPTRagdollAI
   ```

   If the plugin is not allowlisted, you will be warned before it's loaded.

6. **Add API Key environment variable**
   In order to communicate with ragdoll.ai, you will need to create an API key. Find out how to create an API key here: https://docs.ragdoll.ai/

   ``` shell
   RAGDOLL_API_KEY=api-key-here
   ```

7. **Run AutoGPT**
   ``` shell
   ./run.sh --install-plugin-deps
   ```

   We recommend explicitly setting a budget for any task that might be created, e.g.
   Create a task for a text output, with a budget < $0.10
