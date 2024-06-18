// Only Windows
// install WTelegram from nutget

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
                case Process d when d.ProcessName.Contains("", StringComparison.OrdinalIgnoreCase): return "Offline...";

                case Process d when d.MainWindowTitle.Contains("Visual Studio", StringComparison.OrdinalIgnoreCase): return "Playing in VS...";
                case Process d when d.MainWindowTitle.Contains("Youtube", StringComparison.OrdinalIgnoreCase): return "Watching YouTube...";
                case Process d when d.MainWindowTitle.Contains("", StringComparison.OrdinalIgnoreCase): return "Offline...";

            }
            return "";
        }

        static string Config(string what)
        {
            switch (what)
            {
                //replace values
                case "api_id": return "<app_id>";
                case "api_hash": return "<app_hash>";
                case "phone_number": return "+<number>";
                case "verification_code": return "<code>";
                case "first_name": return "";     
                case "last_name": return "";       
                case "password": return "";     //2fa
                default: return null;                  
            }
        }

        var client = new Client(Config);
        await client.Login("+<phone_number>");

        Console.WriteLine($"We are logged-in {client.User.first_name}.");

        Process focusedApplication = GetFocusedApplicationTitle();
        Process oldApplication = focusedApplication;

        while (true)
        {
            focusedApplication = GetFocusedApplicationTitle();

            if (focusedApplication != null)
            {
                if (focusedApplication.MainWindowTitle != oldApplication.MainWindowTitle & getAppTitle(focusedApplication) != "")
                {
                    Console.WriteLine($"New Focused App");
                    oldApplication = focusedApplication;
                    try
                    {
                        Console.WriteLine(focusedApplication.ProcessName);
                        Console.WriteLine(focusedApplication.MainWindowTitle);
                        await client.Account_UpdateProfile(client.User.first_name, client.User.last_name, getAppTitle(focusedApplication));
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
