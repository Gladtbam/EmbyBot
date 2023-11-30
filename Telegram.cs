using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using TL;
using LoadConfig;

namespace WTelegramClient
{
	static class ListenUpdates
	{
		static WTelegram.Client Client;
		static User My;
		static readonly Dictionary<long, User> Users = new();
		static readonly Dictionary<long, ChatBase> Chats = new();

		// go to Project Properties > Debug > Environment variables and add at least these: api_id, api_hash, phone_number
		public static async Task StartBot()
		{
			AppConfig config = Configure.LoadConfigure();
			Console.WriteLine("The program will display updates received for the logged-in user. Press any key to terminate");
			WTelegram.Helpers.Log = (l, s) => System.Diagnostics.Debug.WriteLine(s);
			Client = new WTelegram.Client(config.Telegram.API_ID, config.Telegram.API_HASH, "session");
			using (Client)
			{
				My = await Client.LoginBotIfNeeded(bot_token: config.Telegram.Token);
				Users[My.id] = My;
				// Note: on login, Telegram may sends a bunch of updates/messages that happened in the past and were not acknowledged
				Console.WriteLine($"We are logged-in as {My.username ?? My.first_name + " " + My.last_name} (id {My.id})");
				// We collect all infos about the users/chats so that updates can be printed with their names
				var dialogs = await Client.Messages_GetAllDialogs(); // dialogs = groups/channels/users
				dialogs.CollectUsersChats(Users, Chats);
				Console.ReadKey();
			}
		}

		// if not using async/await, we could just return Task.CompletedTask
		private static async Task Client_OnUpdate(Update updates)
		{
			if (updates is UpdateNewMessage updateNewMessage)
            {
                var message = updateNewMessage.message;
                if (message is Message messageContent)
                {
                    if (messageContent.message == "/start")
                    {
                        Console.WriteLine("start");
                    }
                }
            }
		}
	}
}