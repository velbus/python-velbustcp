from blinker import signal, NamedSignal

on_bus_receive : NamedSignal = signal("on-bus-receive")     # sender:, **kwargs { packet: bytearray }
on_tcp_receive : NamedSignal = signal("on-tcp-receive")     # sender: Client, **kwargs { packet: bytearray }
on_bus_send : NamedSignal = signal("on-bus-send")           # sender:, **kwargs { packet: bytearray }
on_bus_fault : NamedSignal = signal("on-bus-fault")         # sender:, **kwargs {}
on_client_close: NamedSignal = signal("on-client-close")    # sender: Cient, **kwargs {  }

#do_bus_lock : NamedSignal = signal("do-bus-lock")