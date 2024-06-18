using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using TL;
using WTelegram;


[DllImport("user32.dll")]
static extern IntPtr GetForegroundWindow();

[DllImport("user32.dll")]
static extern int GetWindowThreadProcessId(IntPtr hWnd, out int lpdwProcessId);

static Process GetFocusedApplicationTitle()
{
    IntPtr foregroundWindowHandle = GetForegroundWindow();

    if (foregroundWindowHandle == IntPtr.Zero)
    {
        return null;
    }

    int processId;
    GetWindowThreadProcessId(foregroundWindowHandle, out processId);

    try
    {
        Process focusedProcess = Process.GetProcessById(processId);
        return focusedProcess;
    }
    catch (Exception)
    {
        // Handle potential exceptions when getting process name (e.g., access denied)
        return null;
    }
}

static async Task Main()
{
    try
    {
        static string getAppTitle(Process application)
        {
            switch (application)
            {
                case Process d when d.ProcessName.Contains("Visual Studio", StringComparison.OrdinalIgnoreCase): return "Playing in VS...";
                case Process d when d.ProcessName.Contains("Youtube", StringComparison.OrdinalIgnoreCase): return "Watching YouTube...";

                case Process d when d.MainWindowTitle.Contains("Visual Studio", StringComparison.OrdinalIgnoreCase): return "Playing in VS...";
                case Process d when d.MainWindowTitle.Contains("Youtube", StringComparison.OrdinalIgnoreCase): return "Watching YouTube...";

            }
            return "";
        }

        static string Config(string what)
        {
            switch (what)
            {
                case "api_id": return "<api_id>";
                case "api_hash": return "<api_hash>";
                case "phone_number": return "+<number>";
                case "verification_code": return "<code>";
                case "first_name": return "";      // if sign-up is required
                case "last_name": return "";        // if sign-up is required
                case "password": return "";     // if user has enabled 2FA
                default: return null;                  // let WTelegramClient decide the default config
            }
        }

        var client = new Client(Config); 
        await client.Login("+<number>");
        client.DisableUpdates();

        Console.WriteLine($"We are logged-in {client.User.first_name}.");

        Process focusedApplication = GetFocusedApplicationTitle();
        Process oldApplication = focusedApplication;

        while (true)
        {
            focusedApplication = GetFocusedApplicationTitle();

            if (focusedApplication != null)
            {
                string oldBio = "";
                string newBio = getAppTitle(focusedApplication);

                if (newBio == "") { newBio = oldBio; }
                else if (focusedApplication.MainWindowTitle != oldApplication.MainWindowTitle)
                {
                    oldApplication = focusedApplication;
                    oldBio = newBio;
                    try
                    {
                        Console.WriteLine(focusedApplication.MainWindowTitle);
                        await client.Account_UpdateProfile(client.User.first_name, client.User.last_name, newBio);
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"Error updating profile: {ex.Message}");
                    }
                }
            }
            await Task.Delay(5000); // Use Task.Delay for cleaner async/await pattern
        }
    }
    catch (Exception ex) // Catch general exceptions at the top level
    {
        Console.WriteLine($"Unhandled exception: {ex.Message}");
    }
}

await Main();
