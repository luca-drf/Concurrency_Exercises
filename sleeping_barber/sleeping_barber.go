package main

import (
	"flag"
	"fmt"
	"math/rand"
	"sync"
	"time"
)

type Barber struct {
	sleeping bool
	quitting bool
	queue    chan int
	quit     chan int
}

type Client struct {
	id    int
	queue chan int
	wg    *sync.WaitGroup
}

func (b *Barber) run() {
	for {
		select {
		case <-b.quit:
			b.quitting = true
		case id := <-b.queue:
			fmt.Println("Cutting", id)
			time.Sleep(time.Duration(rand.Intn(200)) * time.Millisecond)
		default:
			if b.quitting {
				return
			}
			if !b.sleeping {
				b.sleeping = true
				fmt.Println("Barber is sleeping")
			}
		}
	}
}

func (c *Client) run() {
	defer c.wg.Done()
	time.Sleep(time.Duration(rand.Intn(200)) * time.Millisecond)
	select {
	case c.queue <- c.id:
	default:
		fmt.Println("Client", c.id, "left")
	}
}

func main() {
	buffPtr := flag.Int("buff", 3, "number of chairs (buffer size)")
	clientsPtr := flag.Int("clients", 20, "number of concurrent clients")
	flag.Parse()

	queue := make(chan int, *buffPtr)
	quit := make(chan int)
	var wg sync.WaitGroup

	barber := Barber{false, false, queue, quit}
	go barber.run()

	wg.Add(*clientsPtr)
	for i := 0; i < *clientsPtr; i++ {
		client := Client{i, queue, &wg}
		go client.run()
	}
	wg.Wait()
	quit <- 0
}
