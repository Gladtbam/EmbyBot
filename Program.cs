using LoadConfig;
using DataBase;
using WTelegramClient;
using Microsoft.EntityFrameworkCore;
using System.Threading.Tasks;

namespace EmbyBot
{
    internal class Program
    {
        static async Task Main()
        {
            Configure.InitConfig();
            AppConfig config = Configure.LoadConfigure();
            using var db = new DataBaseContext();
            // db.Database.EnsureCreated();
            // await db.CreateUser("123456", "123456", "112");
            await ListenUpdates.StartBot();
        }
    }
}
