# def _handle_generate_embeddings(self, command):
#         """Handle generating embeddings with the loaded model"""
#         if self.model is None:
#             self.result_queue.put(ModelResponse.error("No model loaded for embeddings"))
#             return

#         try:
#             texts = command["texts"]
#             # LOGGER.info(f"[Device {self.device_id}] Generating embeddings for {len(texts)} texts...")
            
#             texts = [text.replace("\n", " ") for text in texts]
            
#             embeddings = self.model.encode(
#                 texts,
#                 show_progress_bar=False
#             )
                
#             if isinstance(embeddings, list):
#                 raise TypeError(
#                     "Expected embeddings to be a Tensor or numpy array, got list"
#                 )
                
#             # Convert to list for serialization
#             embeddings = embeddings.tolist()
            
#             self.result_queue.put(ModelResponse.success(embeddings))

#         except Exception as e:
#             error_msg = f"Embedding generation failed: {str(e)}"
#             LOGGER.error(f"[Device {self.device_id}] {error_msg}")
#             self.result_queue.put(ModelResponse.error(error_msg))