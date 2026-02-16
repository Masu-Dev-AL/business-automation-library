  const items = $input.all();
  const data = items[0].json;

  const response = await this.helpers.httpRequest({
    method: 'POST',
    url: 'https://graph.facebook.com/v24.0/<PHONE_NUMBER_ID>/messages',
    headers: {
      'Authorization': 'Bearer <WHATSAPP_API_TOKEN>',
      'Content-Type': 'application/json'
    },
    body: {
      messaging_product: 'whatsapp',
      to: '15551234567',
      type: 'template',
      template: {
        name: 'inventory_alert',
        language: { code: 'en_US' },
        components: [{
          type: 'body',
          parameters: [{ type: 'text', text: $input.first().json.whatsapp_text }]
        }]
      }
    },
    json: true
  });

  return [{ json: response }];
