import apollo
while True:
        code = input('>>> ')
        result, error = apollo.run('<stdin>',code)
        if error: print(error.as_string())
        else: print(result)
