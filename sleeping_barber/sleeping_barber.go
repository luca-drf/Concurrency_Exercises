package main

import (
	"flag"
	"fmt"
	"math/rand"
	"sync"
	"time"
)

func barber(queue, quit chan int) {
	sleeping := false
	quitting := false
	for {
		select {
		case <-quit:
			quitting = true
		case client := <-queue:
			fmt.Println("Cutting", client)
			time.Sleep(time.Duration(rand.Intn(200)) * time.Millisecond)
		default:
			if quitting {
				return
			}
			if !sleeping {
				sleeping = true
				fmt.Println("Barber is sleeping")
			}
		}
	}
}

func client(id int, queue chan int, wg *sync.WaitGroup) {
	defer wg.Done()
	time.Sleep(time.Duration(rand.Intn(200)) * time.Millisecond)
	select {
	case queue <- id:
	default:
		fmt.Println("Client", id, "left")
	}
}

func main() {
	buffPtr := flag.Int("buff", 3, "number of chairs (buffer size)")
	clientsPtr := flag.Int("clients", 20, "number of concurrent clients")
	flag.Parse()

	queue := make(chan int, *buffPtr)
	quit := make(chan int)
	var wg sync.WaitGroup

	go barber(queue, quit)

	wg.Add(*clientsPtr)
	for i := 0; i < *clientsPtr; i++ {
		go client(i, queue, &wg)
	}
	wg.Wait()
	quit <- 0
}
